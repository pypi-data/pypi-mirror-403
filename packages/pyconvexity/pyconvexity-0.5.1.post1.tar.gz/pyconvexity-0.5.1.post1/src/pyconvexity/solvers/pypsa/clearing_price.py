"""
Clearing Price Calculator
=========================

Calculates pay-as-clear prices for all buses after network solve.

The clearing price at each bus represents the cost of the marginal MW
that could be supplied to that bus, considering:
- Local generators with spare capacity (dispatch < available capacity)
- Local storage units with spare discharge capacity  
- Imports via uncongested links from adjacent buses

This differs from PyPSA's marginal_price (shadow price) which includes
effects of UC constraints, ramping limits, and other binding constraints.

Algorithm (Single-Pass "Local Marginal"):
=========================================
For each bus at each timestep:
1. Find the cheapest LOCAL source with spare capacity:
   - Generators where p < p_nom * p_max_pu (has spare capacity)
   - Storage units where p < p_nom * p_max_pu (can discharge more)
   - Exclude "unmet load" penalty generators (marginal_cost > threshold)

2. Find the cheapest IMPORT option via uncongested inbound links:
   - For each link where this bus is the destination (bus1):
     - Check if link has spare import capacity: p0 < p_nom * p_max_pu
     - Import price = local_marginal[source_bus] + link.marginal_cost) / link.efficiency
   - For bidirectional links, check both directions

3. clearing_price = min(local_marginal, cheapest_import)

4. If no source has spare capacity (scarcity):
   - Use the unmet load penalty price

Note on Multi-hop Imports:
--------------------------
This single-pass algorithm uses the LOCAL marginal price of adjacent buses,
not their full clearing prices. This means multi-hop import economics are
not captured. For example, if Bus A can import from Bus B, and Bus B can
import cheaply from Bus C, this algorithm won't reflect Bus A's ability
to effectively import from C via B.

This is a deliberate simplification that:
- Avoids iteration/recursion for meshed networks
- Matches a "local market" interpretation where each bus sees instantaneous offers
- Is correct for radial networks (tree topology)

For most practical networks (radial or nearly radial), this gives accurate results.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class LinkInfo:
    """Information about a link for clearing price calculation."""
    link_name: str
    adjacent_bus: str
    marginal_cost: np.ndarray  # Per timestep
    efficiency: float
    spare_capacity_mask: np.ndarray  # Boolean per timestep: True if has spare capacity


@dataclass 
class PriceSetter:
    """Tracks which asset sets the clearing price."""
    asset_name: str
    asset_type: str  # 'generator', 'storage', 'link_import'
    marginal_cost: float
    bus: str


class ClearingPriceCalculator:
    """
    Calculate pay-as-clear prices for all buses in a solved network.
    
    The clearing price is the marginal cost of the cheapest source with
    spare capacity that could supply the next MW to a bus. This differs
    from the LP shadow price (marginal_price) which includes constraint effects.
    
    Example usage:
        calculator = ClearingPriceCalculator()
        clearing_prices = calculator.calculate_all_buses(conn, network, scenario_id)
        # Returns: {'GB_Main': array([45.2, 46.1, ...]), 'FR': array([...]), ...}
    """
    
    def __init__(
        self, 
        unmet_load_threshold: float = 10000.0,
        spare_capacity_tolerance: float = 0.01,
        min_dispatch_threshold: float = 1.0,
        verbose: bool = True,
        include_storage: bool = False,
        min_marginal_cost: float = 1.0,
    ):
        """
        Initialize the calculator.
        
        Args:
            unmet_load_threshold: Marginal cost above which a generator is
                considered an "unmet load" penalty generator and excluded
                from normal clearing price calculation.
            spare_capacity_tolerance: Fraction tolerance for "at capacity".
                A source is considered to have spare capacity if 
                dispatch < available_capacity * (1 - tolerance).
            min_dispatch_threshold: Minimum dispatch (MW) to consider a source
                as "dispatching". Handles numerical noise.
            verbose: Enable detailed logging of price-setting assets.
            include_storage: Whether to include storage units in clearing price.
                Default False because storage marginal_cost in PyPSA is typically
                ~0 (no fuel cost) and doesn't represent the market clearing price.
                In pay-as-clear markets, storage is a price-taker, not a price-setter.
            min_marginal_cost: Minimum marginal cost to consider for price setting.
                Sources with marginal_cost below this are excluded (e.g., to filter
                out renewables with mc=0 that shouldn't set the clearing price).
        """
        self.unmet_load_threshold = unmet_load_threshold
        self.spare_capacity_tolerance = spare_capacity_tolerance
        self.min_dispatch_threshold = min_dispatch_threshold
        self.verbose = verbose
        self.include_storage = include_storage
        self.min_marginal_cost = min_marginal_cost
        
        # Track price setters for logging
        self._price_setters: Dict[str, List[Optional[PriceSetter]]] = {}
    
    def calculate_all_buses(
        self,
        conn,
        network: "pypsa.Network",
        scenario_id: Optional[int] = None,
    ) -> Dict[str, np.ndarray]:
        """
        Calculate clearing prices for all buses in the network.
        
        Args:
            conn: Database connection (for component lookups if needed)
            network: Solved PyPSA Network object
            scenario_id: Scenario ID (for logging)
            
        Returns:
            Dict mapping bus_name -> array of clearing prices per timestep.
            Length of each array equals len(network.snapshots).
        """
        n_periods = len(network.snapshots)
        bus_names = list(network.buses.index)
        
        logger.debug(f"Clearing price calculation: {len(bus_names)} buses, {n_periods} periods")
        
        # Reset price setters tracking
        self._price_setters = {bus: [None] * n_periods for bus in bus_names}
        
        # Step 1: Calculate local marginal price at each bus
        local_marginals, local_setters = self._calculate_local_marginals(network, n_periods)
        
        # Step 2: Build link adjacency map (which buses can import from where)
        link_adjacency = self._build_link_adjacency(network, n_periods)
        
        # Step 3: Calculate clearing prices (single pass)
        clearing_prices = {}
        for bus_name in bus_names:
            clearing_prices[bus_name], setters = self._calculate_bus_clearing_price(
                bus_name,
                local_marginals,
                local_setters,
                link_adjacency,
                n_periods,
            )
            self._price_setters[bus_name] = setters
        
        # Log summary for key buses only
        self._log_clearing_price_summary(clearing_prices, n_periods)
        
        return clearing_prices
    
    def _calculate_local_marginals(
        self, 
        network: "pypsa.Network", 
        n_periods: int
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, List[Optional[PriceSetter]]]]:
        """
        For each bus, calculate the marginal cost of the cheapest local source
        (generator or storage unit) with spare capacity at each timestep.
        
        Returns:
            Tuple of:
            - Dict mapping bus_name -> array of local marginal prices
            - Dict mapping bus_name -> list of PriceSetter objects (one per timestep)
        """
        bus_names = list(network.buses.index)
        local_marginals = {bus: np.full(n_periods, np.inf) for bus in bus_names}
        local_setters = {bus: [None] * n_periods for bus in bus_names}
        
        # Process generators
        gen_stats = self._process_generators(network, n_periods, local_marginals, local_setters)
        
        # Process storage units (discharge as source) - only if enabled
        # By default, storage is excluded because:
        # 1. Storage marginal_cost in PyPSA is typically ~0 (no fuel cost)
        # 2. In pay-as-clear markets, storage is a price-taker, not a price-setter
        # 3. Storage arbitrages between periods; its cost is opportunity cost, not marginal cost
        if self.include_storage:
            storage_stats = self._process_storage_units(network, n_periods, local_marginals, local_setters)
        else:
            storage_stats = {'processed': 0, 'with_spare': 0}
        
        # Process stores (if they can inject power)
        self._process_stores(network, n_periods, local_marginals, local_setters)
        
        logger.debug(f"  Generators: {gen_stats['processed']} processed, {gen_stats['with_spare']} with spare capacity")
        logger.debug(f"  Storage units: {storage_stats['processed']} processed, {storage_stats['with_spare']} with spare capacity")
        
        return local_marginals, local_setters
    
    def _process_generators(
        self,
        network: "pypsa.Network",
        n_periods: int,
        local_marginals: Dict[str, np.ndarray],
        local_setters: Dict[str, List[Optional[PriceSetter]]],
    ) -> Dict[str, int]:
        """Process generators to find local marginals at each bus."""
        stats = {'processed': 0, 'with_spare': 0, 'skipped_unmet': 0, 'skipped_no_pnom': 0}
        
        if network.generators.empty:
            return stats
        
        generators = network.generators
        
        # Get dispatch timeseries
        if hasattr(network.generators_t, 'p') and not network.generators_t.p.empty:
            p_dispatch = network.generators_t.p
        else:
            logger.warning("  No generator dispatch data found (generators_t.p empty)")
            return stats
        
        # Get p_max_pu timeseries (or static)
        if hasattr(network.generators_t, 'p_max_pu') and not network.generators_t.p_max_pu.empty:
            p_max_pu_ts = network.generators_t.p_max_pu
        else:
            p_max_pu_ts = None
        
        # Get marginal_cost timeseries (or static)
        if hasattr(network.generators_t, 'marginal_cost') and not network.generators_t.marginal_cost.empty:
            marginal_cost_ts = network.generators_t.marginal_cost
        else:
            marginal_cost_ts = None
        
        # First pass: regular generators (not unmet load)
        for gen_name in generators.index:
            gen = generators.loc[gen_name]
            bus = gen['bus']
            
            if bus not in local_marginals:
                continue
            
            # Get p_nom
            p_nom = gen.get('p_nom', 0)
            if p_nom <= 0:
                stats['skipped_no_pnom'] += 1
                continue
            
            # Get dispatch values
            if gen_name not in p_dispatch.columns:
                continue
            p_values = p_dispatch[gen_name].values
            if len(p_values) != n_periods:
                p_values = self._pad_or_truncate(p_values, n_periods)
            
            # Get p_max_pu values
            if p_max_pu_ts is not None and gen_name in p_max_pu_ts.columns:
                p_max_pu_values = p_max_pu_ts[gen_name].values
            else:
                p_max_pu_values = np.full(n_periods, gen.get('p_max_pu', 1.0))
            if len(p_max_pu_values) != n_periods:
                p_max_pu_values = self._pad_or_truncate(p_max_pu_values, n_periods)
            
            # Get marginal_cost values
            if marginal_cost_ts is not None and gen_name in marginal_cost_ts.columns:
                mc_values = marginal_cost_ts[gen_name].values
            else:
                mc_values = np.full(n_periods, gen.get('marginal_cost', 0.0))
            if len(mc_values) != n_periods:
                mc_values = self._pad_or_truncate(mc_values, n_periods)
            
            # Skip unmet load generators (handle in second pass)
            if np.any(mc_values > self.unmet_load_threshold):
                stats['skipped_unmet'] += 1
                continue
            
            stats['processed'] += 1
            
            # Calculate available capacity
            available = p_nom * p_max_pu_values
            
            # Find timesteps where generator has spare capacity
            spare_capacity_mask = p_values < available * (1 - self.spare_capacity_tolerance)
            n_spare = spare_capacity_mask.sum()
            
            if n_spare > 0:
                stats['with_spare'] += 1
            
            # Log details for this generator
            if self.verbose and n_spare > 0:
                mean_mc = np.mean(mc_values)
                mean_dispatch = np.mean(p_values)
                mean_available = np.mean(available)
                logger.debug(f"    {gen_name} @ {bus}: mc={mean_mc:.2f}, dispatch={mean_dispatch:.1f}MW, available={mean_available:.1f}MW, spare_periods={n_spare}/{n_periods}")
            
            # Update local marginal where this generator is cheaper and has spare capacity
            # Also filter by min_marginal_cost (e.g., to exclude renewables with mc=0)
            for t in range(n_periods):
                if (spare_capacity_mask[t] 
                    and mc_values[t] >= self.min_marginal_cost
                    and mc_values[t] < local_marginals[bus][t]):
                    local_marginals[bus][t] = mc_values[t]
                    local_setters[bus][t] = PriceSetter(
                        asset_name=gen_name,
                        asset_type='generator',
                        marginal_cost=mc_values[t],
                        bus=bus
                    )
        
        # Second pass: handle unmet load generators (only set price if no other source available)
        for gen_name in generators.index:
            gen = generators.loc[gen_name]
            bus = gen['bus']
            
            if bus not in local_marginals:
                continue
            
            p_nom = gen.get('p_nom', 0)
            if p_nom <= 0:
                continue
            
            # Get marginal_cost values
            if marginal_cost_ts is not None and gen_name in marginal_cost_ts.columns:
                mc_values = marginal_cost_ts[gen_name].values
            else:
                mc_values = np.full(n_periods, gen.get('marginal_cost', 0.0))
            if len(mc_values) != n_periods:
                mc_values = self._pad_or_truncate(mc_values, n_periods)
            
            # Only process unmet load generators
            if not np.any(mc_values > self.unmet_load_threshold):
                continue
            
            # Get dispatch and check spare capacity
            if gen_name not in p_dispatch.columns:
                continue
            p_values = p_dispatch[gen_name].values
            if len(p_values) != n_periods:
                p_values = self._pad_or_truncate(p_values, n_periods)
            
            if p_max_pu_ts is not None and gen_name in p_max_pu_ts.columns:
                p_max_pu_values = p_max_pu_ts[gen_name].values
            else:
                p_max_pu_values = np.full(n_periods, gen.get('p_max_pu', 1.0))
            if len(p_max_pu_values) != n_periods:
                p_max_pu_values = self._pad_or_truncate(p_max_pu_values, n_periods)
            
            available = p_nom * p_max_pu_values
            spare_capacity_mask = p_values < available * (1 - self.spare_capacity_tolerance)
            
            # Only use unmet load price where local_marginal is still inf (no other source)
            n_set = 0
            for t in range(n_periods):
                if spare_capacity_mask[t] and np.isinf(local_marginals[bus][t]):
                    local_marginals[bus][t] = mc_values[t]
                    local_setters[bus][t] = PriceSetter(
                        asset_name=gen_name,
                        asset_type='unmet_load',
                        marginal_cost=mc_values[t],
                        bus=bus
                    )
                    n_set += 1
            
            if n_set > 0:
                logger.debug(f"    UNMET LOAD {gen_name}: set price for {n_set} periods (no other source)")
        
        return stats
    
    def _process_storage_units(
        self,
        network: "pypsa.Network",
        n_periods: int,
        local_marginals: Dict[str, np.ndarray],
        local_setters: Dict[str, List[Optional[PriceSetter]]],
    ) -> Dict[str, int]:
        """Process storage units (discharge capacity) to find local marginals."""
        stats = {'processed': 0, 'with_spare': 0}
        
        if network.storage_units.empty:
            return stats
        
        storage_units = network.storage_units
        
        # Get dispatch timeseries (positive = discharge)
        if hasattr(network.storage_units_t, 'p') and not network.storage_units_t.p.empty:
            p_dispatch = network.storage_units_t.p
        else:
            logger.warning("  No storage unit dispatch data found")
            return stats
        
        for su_name in storage_units.index:
            su = storage_units.loc[su_name]
            bus = su['bus']
            
            if bus not in local_marginals:
                continue
            
            # Get p_nom (discharge capacity)
            p_nom = su.get('p_nom', 0)
            if p_nom <= 0:
                continue
            
            # Get dispatch values
            if su_name not in p_dispatch.columns:
                continue
            p_values = p_dispatch[su_name].values
            if len(p_values) != n_periods:
                p_values = self._pad_or_truncate(p_values, n_periods)
            
            # Get p_max_pu
            if hasattr(network.storage_units_t, 'p_max_pu') and su_name in network.storage_units_t.p_max_pu.columns:
                p_max_pu_values = network.storage_units_t.p_max_pu[su_name].values
            else:
                p_max_pu_values = np.full(n_periods, su.get('p_max_pu', 1.0))
            if len(p_max_pu_values) != n_periods:
                p_max_pu_values = self._pad_or_truncate(p_max_pu_values, n_periods)
            
            # Get marginal_cost
            if hasattr(network.storage_units_t, 'marginal_cost') and su_name in network.storage_units_t.marginal_cost.columns:
                mc_values = network.storage_units_t.marginal_cost[su_name].values
            else:
                mc_values = np.full(n_periods, su.get('marginal_cost', 0.0))
            if len(mc_values) != n_periods:
                mc_values = self._pad_or_truncate(mc_values, n_periods)
            
            stats['processed'] += 1
            
            # Calculate available discharge capacity
            available = p_nom * p_max_pu_values
            
            # Spare capacity for discharge: current discharge < max discharge
            spare_capacity_mask = p_values < available * (1 - self.spare_capacity_tolerance)
            n_spare = spare_capacity_mask.sum()
            
            if n_spare > 0:
                stats['with_spare'] += 1
            
            if self.verbose and n_spare > 0:
                logger.debug(f"    {su_name} @ {bus}: mc={np.mean(mc_values):.2f}, spare_periods={n_spare}/{n_periods}")
            
            # Update local marginal
            for t in range(n_periods):
                if spare_capacity_mask[t] and mc_values[t] < local_marginals[bus][t]:
                    local_marginals[bus][t] = mc_values[t]
                    local_setters[bus][t] = PriceSetter(
                        asset_name=su_name,
                        asset_type='storage',
                        marginal_cost=mc_values[t],
                        bus=bus
                    )
        
        return stats
    
    def _process_stores(
        self,
        network: "pypsa.Network",
        n_periods: int,
        local_marginals: Dict[str, np.ndarray],
        local_setters: Dict[str, List[Optional[PriceSetter]]],
    ) -> None:
        """Process stores (if they can inject power) to find local marginals."""
        if network.stores.empty:
            return
        
        # Stores are complex - skip for now
        # They don't have a fixed p_nom like generators/storage_units
        logger.debug(f"  Skipping {len(network.stores)} stores (complex capacity constraints)")
    
    def _build_link_adjacency(
        self,
        network: "pypsa.Network",
        n_periods: int,
    ) -> Dict[str, List[LinkInfo]]:
        """
        Build a map of bus -> list of inbound link options.
        """
        link_adjacency: Dict[str, List[LinkInfo]] = {}
        
        if network.links.empty:
            return link_adjacency
        
        links = network.links
        
        # Get link flow timeseries
        if hasattr(network.links_t, 'p0') and not network.links_t.p0.empty:
            p0_dispatch = network.links_t.p0
        else:
            p0_dispatch = None
            logger.warning("  No link flow data found (links_t.p0 empty)")
        
        for link_name in links.index:
            link = links.loc[link_name]
            bus0 = link['bus0']
            bus1 = link['bus1']
            
            p_nom = link.get('p_nom', 0)
            if p_nom <= 0:
                continue
            
            efficiency = link.get('efficiency', 1.0)
            if pd.isna(efficiency) or efficiency <= 0:
                efficiency = 1.0
            
            # Get marginal_cost
            if hasattr(network.links_t, 'marginal_cost') and link_name in network.links_t.marginal_cost.columns:
                mc_values = network.links_t.marginal_cost[link_name].values
            else:
                mc_values = np.full(n_periods, link.get('marginal_cost', 0.0))
            if len(mc_values) != n_periods:
                mc_values = self._pad_or_truncate(mc_values, n_periods)
            
            # Get p_max_pu
            if hasattr(network.links_t, 'p_max_pu') and link_name in network.links_t.p_max_pu.columns:
                p_max_pu_values = network.links_t.p_max_pu[link_name].values
            else:
                p_max_pu_values = np.full(n_periods, link.get('p_max_pu', 1.0))
            if len(p_max_pu_values) != n_periods:
                p_max_pu_values = self._pad_or_truncate(p_max_pu_values, n_periods)
            
            # Get p_min_pu
            if hasattr(network.links_t, 'p_min_pu') and link_name in network.links_t.p_min_pu.columns:
                p_min_pu_values = network.links_t.p_min_pu[link_name].values
            else:
                p_min_pu_values = np.full(n_periods, link.get('p_min_pu', 0.0))
            if len(p_min_pu_values) != n_periods:
                p_min_pu_values = self._pad_or_truncate(p_min_pu_values, n_periods)
            
            # Get actual flow
            if p0_dispatch is not None and link_name in p0_dispatch.columns:
                p0_values = p0_dispatch[link_name].values
            else:
                p0_values = np.zeros(n_periods)
            if len(p0_values) != n_periods:
                p0_values = self._pad_or_truncate(p0_values, n_periods)
            
            # Direction 1: bus0 -> bus1 (positive flow)
            max_forward = p_nom * p_max_pu_values
            spare_forward = p0_values < max_forward * (1 - self.spare_capacity_tolerance)
            
            if bus1 not in link_adjacency:
                link_adjacency[bus1] = []
            link_adjacency[bus1].append(LinkInfo(
                link_name=link_name,
                adjacent_bus=bus0,
                marginal_cost=mc_values,
                efficiency=efficiency,
                spare_capacity_mask=spare_forward,
            ))
            
            logger.debug(f"    {link_name}: {bus0} -> {bus1}, p_nom={p_nom:.0f}MW, eff={efficiency:.2f}, spare_periods={spare_forward.sum()}")
            
            # Direction 2: bus1 -> bus0 (negative flow, if allowed)
            if np.any(p_min_pu_values < 0):
                max_reverse = p_nom * np.abs(p_min_pu_values)
                current_reverse = np.maximum(-p0_values, 0)
                spare_reverse = current_reverse < max_reverse * (1 - self.spare_capacity_tolerance)
                
                if bus0 not in link_adjacency:
                    link_adjacency[bus0] = []
                link_adjacency[bus0].append(LinkInfo(
                    link_name=f"{link_name}_reverse",
                    adjacent_bus=bus1,
                    marginal_cost=mc_values,
                    efficiency=efficiency,
                    spare_capacity_mask=spare_reverse,
                ))
                
                logger.debug(f"    {link_name}_reverse: {bus1} -> {bus0}, spare_periods={spare_reverse.sum()}")
        
        return link_adjacency
    
    def _calculate_bus_clearing_price(
        self,
        bus_name: str,
        local_marginals: Dict[str, np.ndarray],
        local_setters: Dict[str, List[Optional[PriceSetter]]],
        link_adjacency: Dict[str, List[LinkInfo]],
        n_periods: int,
    ) -> Tuple[np.ndarray, List[Optional[PriceSetter]]]:
        """
        Calculate clearing price for a single bus.
        
        Returns:
            Tuple of (clearing_prices array, list of PriceSetter for each timestep)
        """
        clearing_prices = np.copy(local_marginals.get(bus_name, np.full(n_periods, np.inf)))
        setters = list(local_setters.get(bus_name, [None] * n_periods))
        
        # Check import options
        n_import_better = 0
        if bus_name in link_adjacency:
            for link_info in link_adjacency[bus_name]:
                adj_bus = link_info.adjacent_bus
                adj_marginal = local_marginals.get(adj_bus, np.full(n_periods, np.inf))
                
                for t in range(n_periods):
                    if link_info.spare_capacity_mask[t]:
                        # Import price = (adjacent marginal + link cost) / efficiency
                        import_price = (adj_marginal[t] + link_info.marginal_cost[t]) / link_info.efficiency
                        if import_price < clearing_prices[t]:
                            clearing_prices[t] = import_price
                            setters[t] = PriceSetter(
                                asset_name=link_info.link_name,
                                asset_type='link_import',
                                marginal_cost=import_price,
                                bus=bus_name
                            )
                            n_import_better += 1
        
        # Handle remaining inf values (true scarcity)
        n_scarcity = np.isinf(clearing_prices).sum()
        clearing_prices = np.where(np.isinf(clearing_prices), self.unmet_load_threshold * 10, clearing_prices)
        
        # Log warning only for problematic buses
        n_zeros = (clearing_prices == 0).sum()
        if n_zeros > 0 or n_scarcity > 0:
            logger.warning(f"  {bus_name}: zeros={n_zeros}, scarcity={n_scarcity}")
        
        return clearing_prices, setters
    
    def _log_clearing_price_summary(
        self,
        clearing_prices: Dict[str, np.ndarray],
        n_periods: int,
    ) -> None:
        """Log compact summary of clearing prices."""
        # Log summary for key buses (GB_Main if present, otherwise all)
        key_buses = ['GB_Main'] if 'GB_Main' in clearing_prices else list(clearing_prices.keys())[:3]
        
        for bus_name in key_buses:
            prices = clearing_prices.get(bus_name)
            if prices is None:
                continue
                
            setters = self._price_setters.get(bus_name, [])
            
            # Count price setters by type
            setter_counts: Dict[str, int] = {}
            for setter in setters:
                key = setter.asset_type if setter else 'none'
                setter_counts[key] = setter_counts.get(key, 0) + 1
            
            # Summary stats
            valid = prices[(prices > 0) & (prices < self.unmet_load_threshold)]
            setters_str = ", ".join(f"{k}:{v}" for k, v in sorted(setter_counts.items(), key=lambda x: -x[1]))
            
            if len(valid) > 0:
                logger.info(f"  Clearing prices [{bus_name}]: mean=£{np.mean(valid):.2f}, range=[£{np.min(valid):.2f}, £{np.max(valid):.2f}], setters: {setters_str}")
    
    def _pad_or_truncate(self, arr: np.ndarray, target_length: int) -> np.ndarray:
        """Pad array with last value or truncate to target length."""
        arr = np.asarray(arr)
        if len(arr) >= target_length:
            return arr[:target_length]
        else:
            padding = np.full(target_length - len(arr), arr[-1] if len(arr) > 0 else 0)
            return np.concatenate([arr, padding])
