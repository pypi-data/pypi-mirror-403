from __future__ import annotations

import datetime as dt
import math
from collections.abc import Iterable

import numpy as np
import pandas as pd

def _common_str(self) -> str:
    acronym = getattr(self, '_acronym', type(self).__name__)
    name = getattr(self, 'name', '')
    return f'[{acronym}] {name}'


def _common_repr(self) -> str:
    def fmt(v):
        if isinstance(v, (int, float, str, bool, type(None))):
            return repr(v)
        if hasattr(v, 'name') and not isinstance(v, (str, bytes)):
            return repr(getattr(v, 'name'))
        if isinstance(v, dict):
            return f'<dict len={len(v)}>'
        if isinstance(v, (list, tuple, set)):
            return f'<{type(v).__name__} len={len(v)}>'
        shape = getattr(v, 'shape', None)
        if shape is not None:
            try:
                r, c = shape
                return f'<{type(v).__name__} shape={r}x{c}>'
            except Exception:
                return f'<{type(v).__name__} shape={shape}>'
        return repr(v)

    names: list[str] = []
    for cls in type(self).__mro__:
        slots = getattr(cls, '__slots__', ())
        names.extend((slots,) if isinstance(slots, str) else slots)

    seen = set()
    items: list[tuple[str, object]] = []
    for name in names:
        if name and name not in seen and hasattr(self, name):
            seen.add(name)
            items.append((name, getattr(self, name)))

    if not items and hasattr(self, '__dict__'):
        items = list(self.__dict__.items())

    body = ',\n  '.join(f'{k}={fmt(v)}' for k, v in items)
    return f'{type(self).__name__}(\n  {body}\n)'


class Calendar:
    """
    Calendar class.
    """

    name:          str
    working_days:  set[int]
    hours_per_day: float
    holidays:      set[dt.date]

    __slots__ = (
        'name',
        'working_days',
        'holidays',
        'hours_per_day',
    )
    
    _acronym = 'C'
    __str__  = _common_str
    __repr__ = _common_repr

    _ALLOWED_STRDATE_FORMATS = (
        '%Y%m%d', 
        '%Y-%m-%d', 
        '%Y/%m/%d', 
        '%Y.%m.%d'
    )
    _WEEKDAYS = set(range(7))

    def __init__(
        self, 
        name:          str                                                        = 'Calendar',
        working_days:  None | Iterable[int]                                       = None,
        hours_per_day: float                                                      = 8.0,
        holidays:      None | Iterable[int | float | str | dt.datetime | dt.date] = None,
    ):
        self.name =         str(name)
        self.working_days = {0, 1, 2, 3, 4, 5, 6} if working_days is None else self._evaluate_working_days(working_days)
        self.holidays     = set()                 if holidays     is None else {self._parse_date(hday) for hday in holidays}

        self.hours_per_day = float(hours_per_day) 
        if not 0.0 < self.hours_per_day <= 24.0:
            raise ValueError(f'0.0 < hours_per_day <= 24.0, got {self.hours_per_day}')
    
    def _evaluate_working_days(
        self, 
        working_days: Iterable[int]
    ) -> set[int]:
        wdays: set[int] = set()
        for wday in working_days:
            if isinstance(wday, int) and not isinstance(wday, bool):
                if wday in self._WEEKDAYS:
                    wdays.add(wday)
                else:
                    raise ValueError(f'0 <= wday <= 6, got {wday}')      
            else:
                raise TypeError(f'type(wday) = int, got {type(wday)}')      
        if not wdays:
            raise ValueError(f'working_days is empty, must contain at least 0, 1, 2, 3, 4, 5, or 6')
        return wdays
        
    def _is_working_day(
        self, 
        date: dt.date
    ) -> bool:
        return date.weekday() in self.working_days and date not in self.holidays

    def _workday(
        self, 
        start_date: dt.date, 
        days:       int
    ) -> dt.date:
        current_date = start_date
        remaining_days = abs(round(days))
        if remaining_days == 0:
            return current_date
        step = dt.timedelta(days=1 if days >= 0 else -1)
        while remaining_days:
            current_date += step    
            if self._is_working_day(current_date):
                remaining_days -= 1
        return current_date
    
    def _networkdays(
        self, 
        start_date:  dt.date, 
        finish_date: dt.date
    ) -> int:
        if start_date < finish_date:
            sign = 1
        elif start_date == finish_date:
            return 1 if self._is_working_day(start_date) else 0
        else:
            start_date, finish_date = finish_date, start_date
            sign = -1
        wdays = self.working_days
        hdays = self.holidays
        total_days = (finish_date - start_date).days + 1
        full_weeks, extra_days = divmod(total_days, 7)
        count = full_weeks * len(wdays)
        start_weekday = start_date.weekday()
        count += sum(((start_weekday + i) % 7) in wdays for i in range(extra_days))
        if hdays:
            for h in hdays:
                if start_date <= h <= finish_date and h.weekday() in wdays:
                    count -= 1
        return sign * count

    @staticmethod
    def _parse_date(
        date_val: dt.date | dt.datetime | str | int | float,
    ) -> dt.date:
        if isinstance(date_val, dt.datetime):
            return date_val.date()
        if isinstance(date_val, dt.date):
            return date_val
        if isinstance(date_val, int | float):
            return dt.datetime.strptime(str(int(date_val)), '%Y%m%d').date()
        if isinstance(date_val, str):
            s = date_val.strip()
            for fmt in Calendar._ALLOWED_STRDATE_FORMATS:
                try:
                    return dt.datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
        raise TypeError(f'type(date_val) not in (dt.date, dt.datetime, str, int, float), got {type(date_val)}')


class Resource:
    """
    Resource class.
    """

    name:          str
    resource_type: str
    unit_cost:     float
    availability:  float
    
    _allocations:  dict[str, tuple[Activity, float]]
    _total_cost:   float

    __slots__ = (
        'name',
        'resource_type',
        'unit_cost',
        'availability',
        '_allocations',
        '_total_cost',
    )
    
    _acronym = 'R'
    __str__  = _common_str
    __repr__ = _common_repr

    _ALLOWED_RESOURCE_TYPES = ('work', 'material', 'cost')

    def __init__(
        self,
        name:          str   = 'Resource',
        resource_type: str   = 'work',
        unit_cost:     float = 0.0,
        availability:  float = math.inf,
    ):  
        
        # Basic
        self.name = str(name)
        self.resource_type = self._evaluate_resource_type(resource_type)

        self.unit_cost = float(unit_cost)
        if self.unit_cost < 0:
            raise ValueError(f'unit_cost >= 0.0, got {unit_cost}')
        
        self.availability = float(availability)
        if self.availability < 0:
            raise ValueError(f'availability >= 0.0, got {availability}')

        # Scheduling
        self._allocations: dict[str, tuple[Activity, float]] = {}
        self._total_cost:  float                             = 0.0

    def _evaluate_resource_type(
        self,
        resource_type: str
    ) -> str:
        if not isinstance(resource_type, str):
            raise TypeError(f'resource_type must be str, got {type(resource_type)}')
        s = resource_type.strip().lower()
        if s in self._ALLOWED_RESOURCE_TYPES:
            return s
        else:
            raise TypeError(f'resource_type not in {self._ALLOWED_RESOURCE_TYPES}, got {type(s)}')
        raise ValueError(f'resource_type must be one of {self._ALLOWED_RESOURCE_TYPES}, got {resource_type!r}')
    
    @property
    def allocations(self) -> dict[str, tuple[Activity, float]]:
        return self._allocations
    
    @property
    def total_cost(self) -> float:
        return self._total_cost


class Activity:
    """
    Activity class.
    """
    
    name:                  str

    predecessors:          dict[str, tuple[Activity, str, float]]
    successors:            dict[str, tuple[Activity, str, float]]

    baseline_resources:    dict[str, tuple[Resource,      float]]
    baseline_duration:     float
    effort_driven:         bool
    resources:             dict[str, tuple[Resource,      float]]
    duration:              float

    calendar:              Calendar | None
    es:                    dt.date  | None
    ef:                    dt.date  | None
    ls:                    dt.date  | None
    lf:                    dt.date  | None
    es_constraint:         bool
    ef_constraint:         bool
    ls_constraint:         bool
    lf_constraint:         bool
    slack:                 int      | None
    critical:              bool     | None

    direct_cost:           float
    overhead_rate:         float
    overhead_criterion:    str
    indirect_cost:         float
    total_cost:            float

    duration_distribution: str
    duration_mean:         float
    duration_stdev:        float
    duration_params:       dict
    cost_distribution:     str
    cost_mean:             float
    cost_stdev:            float
    cost_params:           dict
    criticality:           float

    control_accounts:      dict[str, ControlAccount]
    records:               dict[int, dict]
    as_date:               dt.date | None
    as_days:               int     | None
    af_date:               dt.date | None
    af_days:               int     | None

    project:               Project | None

    __slots__ = (
        'name',

        'predecessors', 
        'successors',

        'baseline_resources', 
        'baseline_duration',
        'effort_driven',
        'resources',
        'duration',
        'calendar',

        'es', 'ef', 
        'ls', 'lf',
        'es_constraint', 
        'ef_constraint',
        'ls_constraint', 
        'lf_constraint',
        'slack', 
        'critical',

        'direct_cost',
        'overhead_rate', 
        'overhead_criterion',
        'indirect_cost',
        'total_cost',

        'duration_distribution', 
        'duration_mean', 
        'duration_stdev', 
        'duration_params',
        'cost_distribution', 
        'cost_mean', 
        'cost_stdev', 
        'cost_params', 
        'criticality',

        'control_accounts',
        'records',
        '_as_date', 
        '_as_days',
        '_af_date', 
        '_af_days',

        'project',
    )
    _acronym = 'A'
    __str__  = _common_str
    __repr__ = _common_repr

    def __init__(
        self,

        name:                  str                                           = 'Activity',
        predecessors:          dict[str, tuple[Activity, str, float]] | None = None,

        baseline_resources:    dict[str, tuple[Resource,      float]] | None = None,
        baseline_duration:     float                                         = 0.0,
        effort_driven:         bool | int | float                            = True,
        resources:             dict[str, tuple[Resource,      float]] | None = None,

        calendar:              None | Calendar                                  = None,
        es:                    None | int | float | str | dt.date | dt.datetime = None,
        ef:                    None | int | float | str | dt.date | dt.datetime = None,
        ls:                    None | int | float | str | dt.date | dt.datetime = None,
        lf:                    None | int | float | str | dt.date | dt.datetime = None,

        direct_cost:           None | float = None,
        overhead_rate:                float = 0.0,
        overhead_criterion:    str          = 'direct_cost',
        indirect_cost:         None | float = None,
        total_cost:            None | float = None,

        duration_distribution: str          = 'fixed',
        duration_mean:         None | float = None,
        duration_stdev:               float = 0.0,
        duration_params:       dict | None  = None,
        cost_distribution:     str          = 'fixed',
        cost_mean:             None | float = None,
        cost_stdev:                   float = 0.0,
        cost_params:           dict | None  = None,

        as_date:               None | int | float | str | dt.date | dt.datetime = None,
        af_date:               None | int | float | str | dt.date | dt.datetime = None,

        project:               None | Project = None
    ): 
        
        # Basic
        self.name = str(name)

        # Planning
        self.predecessors = predecessors if predecessors is not None else {}       
        self.successors   =                                               {}

        # Resources, Duration
        self.baseline_resources = baseline_resources if baseline_resources is not None else {}
        self.baseline_duration =  float(baseline_duration)
        self.resources =          resources          if resources          is not None else {}
        self.effort_driven =      bool(effort_driven)
        self.duration =           self._calculate_duration()

        # Scheduling
        self.calendar =      None if calendar is None else calendar
        self.es =            None if es       is None else Calendar._parse_date(es)
        self.ef =            None if ef       is None else Calendar._parse_date(ef)
        self.ls =            None if ls       is None else Calendar._parse_date(ls)
        self.lf =            None if lf       is None else Calendar._parse_date(lf)
        self.es_constraint = self.es is not None
        self.ef_constraint = self.ef is not None
        self.ls_constraint = self.ls is not None
        self.lf_constraint = self.lf is not None
        if self.calendar is not None and self.es is not None and self.ls is not None:
            self.slack    = self.calendar._networkdays(self.es, self.ls) - 1
            self.critical = self.slack <= 0
        else:
            self.slack    = None
            self.critical = None

        # Costs
        self.direct_cost =        self._calculate_direct_cost()   if direct_cost   is None else direct_cost
        self.overhead_rate =      float(overhead_rate)
        self.overhead_criterion = overhead_criterion
        self.indirect_cost =      self._calculate_indirect_cost() if indirect_cost is None else indirect_cost
        self.total_cost =         self._calculate_total_cost()    if total_cost    is None else total_cost

        # Allocations
        self._add_allocations()

        # Monitoring
        self._as_date = None
        self._as_days = None
        if as_date is not None:
            self.as_date = as_date

        self._af_date = None
        self._af_days = None
        if af_date is not None:
            self.af_date = af_date

        self.records          = {}
        self.control_accounts = {}
        self._add_controlaccounts()

        self.project = project

        # MC Simulation
        ## Duration
        self.duration_distribution = duration_distribution
        self.duration_mean =         self.duration   if duration_mean   is None else float(duration_mean)
        self.duration_stdev =        float(duration_stdev)
        self.duration_params =       {}              if duration_params is None else duration_params 
        ## Cost
        self.cost_distribution =     cost_distribution
        self.cost_mean =             self.total_cost if cost_mean       is None else float(cost_mean)
        self.cost_stdev =            float(cost_stdev)
        self.cost_params =           {}              if cost_params     is None else cost_params  
        ## Schedule
        self.criticality =           0.0

    # Duration

    def _calculate_duration(self) -> float:
        b_res = self.baseline_resources
        if b_res and self.effort_driven:
            res = self.resources
            if res:
                scaling_factors: set[float] = set()
                for r, requirement in b_res.values():
                    if r.name in res:
                        allocated = res[r.name][1]
                        if r.resource_type == 'work':
                            if allocated > 0:
                                scaling_factors.add(allocated / requirement)
                            else:
                                return math.inf
                        else:
                            if allocated >= requirement:
                                scaling_factors.add(1.0)
                            else:
                                return math.inf
                    else:
                        return math.inf
                else:
                    return self.baseline_duration / min(scaling_factors, default=1.0)
            else:
                return math.inf
        else:
            return self.baseline_duration

    # Costs

    def _calculate_direct_cost(self) -> float:
        pd_days = self.baseline_duration
        total = 0.0
        for r, units in self.resources.values():
            total += r.unit_cost * units * pd_days if r.resource_type == 'work' else r.unit_cost * units
        return total

    def _calculate_indirect_cost(self) -> float:
        return self.duration * self.overhead_rate
    
    def _calculate_total_cost(self) -> float:
        return self.direct_cost + self.indirect_cost
    
    # Allocations

    def _add_allocations(self) -> None:
        if self.direct_cost > 0.0 and not self.baseline_resources and not self.resources:
            r = Resource(
                name = f'[{self.name}] Direct', 
                resource_type = 'cost', 
                unit_cost = self.direct_cost,
            )
            self.baseline_resources[r.name] = (r, 1.0)
            self.resources[r.name] = (r, 1.0)
        for r, units in self.resources.values():
            r.allocations[self.name] = (self, float(units))

    # Monitoring
    
    ## CAs

    def _add_controlaccounts(self) -> None:
        for r, u in self.resources.values():
            ca = ControlAccount(
                name=f'{self.name}-{r.name}',
                activity=self,
                resource=r,
                units=u,
            )
            self.control_accounts[ca.name] = ca    

    ## AS

    @property
    def as_date(self) -> dt.date | None:
        return self._as_date

    @property
    def as_days(self) -> int | None:
        return self._as_days

    @as_date.setter
    def as_date(
        self, 
        value: dt.date | dt.datetime | str | int | float | None
    ) -> None:
        if value is None:
            self._as_date = None
            self._as_days = None
            return
        cal = self.calendar
        if cal is not None:
            self._as_date = cal._parse_date(value)
        else:
            self._as_date = Calendar(working_days=[0, 1, 2, 3, 4, 5, 6])._parse_date(value)
        if cal is not None and self.es is not None:
            self._as_days = cal._networkdays(self.es, self._as_date) - 1
        else:
            self._as_days = None

    ## AF

    @property
    def af_date(self) -> dt.date | None:
        return self._af_date

    @property
    def af_days(self) -> int | None:
        return self._af_days
    
    @af_date.setter
    def af_date(
        self, 
        value: dt.date | dt.datetime | str | int | float | None
    ) -> None:
        if value is None:
            self._af_date = None
            self._af_days = None
            return
        cal = self.calendar
        self._af_date = Calendar._parse_date(value)
        if cal is not None and self.es is not None:
            self._af_days = cal._networkdays(self.es, self._af_date) - 1
        else:
            self._af_days = None

    ## EVA

    def update_record(
        self, 
        date_key: dt.date | dt.datetime | str | int | float, 
        wp: float
    ) -> None:
        
        # Calendar
        cal = self.calendar
        if cal is None:
            raise ValueError()

        # AS, AT
        at_date = cal._parse_date(date_key)

        as_date = self.as_date
        as_days = self.as_days

        af_date = self.af_date
        af_days = self.af_days
        
        if as_date is not None:
            at_days = cal._networkdays(as_date, at_date)
        else:
            at_days = None

        # BAC, PD
        bac =     self.total_cost
        pd_days = self.duration
        pd_date = self.ef

        # WS
        if as_date is not None and pd_days > 0:
            if at_date < as_date:
                ws = 0.0
            else:
                nd = cal._networkdays(as_date, at_date)
                ws = max(
                    0.0, 
                    min(nd, pd_days) / pd_days
                )
        else:
            ws = 0.0
        
        # AC
        ac = 0.0
        for ca in self.control_accounts.values():
            if date_key in ca.records:
                ac_record = ca.records[date_key]['AC']
            else:
                prev_dates = [d for d in ca.records if d <= date_key]
                ac_record = ca.records[max(prev_dates)]['AC'] if prev_dates else None
            if ac_record is not None:
                ac += ac_record

        # PV, EV, CV, SV, CPI, SPI, CEACs, TEACs
        pv = bac * ws                   
        ev = bac * wp                   
        cv = ev - ac                    
        sv = ev - pv                    
        cpi = ev / ac if ac != 0.0 else 1.0 
        spi = ev / pv if pv != 0.0 else 1.0
        ceac_cv = bac - cv
        ceac_cpi = bac / cpi if cpi != 0 else math.inf
        teac_spi_days = pd_days / spi if spi != 0 else math.inf
        teac_spi_date = cal._workday(as_date, teac_spi_days) if (as_date is not None and teac_spi_days != math.inf) else pd.NaT

        # Add Record
        self.records[date_key] = {
            'AS[Date]':         as_date,
            'AF[Date]':         af_date,
            'PD[Date]':         pd_date,
            'AT[Date]':         at_date,
            'AS[Days]':         as_days,
            'AF[Days]':         af_days,
            'PD[Days]':         pd_days,
            'AT[Days]':         at_days,
            'BAC':              bac,
            'WS':               ws, 
            'WP':               wp, 
            'PV':               pv, 
            'EV':               ev, 
            'AC':               ac,
            'CV':               cv,
            'SV':               sv,
            'CPI':              cpi,
            'SPI':              spi,
            'EAC_CV':           ceac_cv,
            'EAC_CPI':          ceac_cpi,
            'EAC(t)_SPI[Date]': teac_spi_date,
            'EAC(t)_SPI[Days]': teac_spi_days
        }

    def df_eva(self) -> pd.DataFrame:
        recs = self.records
        for date_key in sorted(recs):
            wp = max(
                (rec.get('WP', 0.0)
                for rec_date, rec in recs.items()
                if rec_date <= date_key),
                default=0.0,
            )
            for ca in self.control_accounts.values():
                ac = max(
                    (rec.get('AC', 0.0)
                    for rec_date, rec in ca.records.items()
                    if rec_date <= date_key),
                    default=0.0,
                )
                ca.update_record(date_key, ac)
            self.update_record(date_key, wp)
            if self.project is not None:
                self.project.update_record(date_key)
        return pd.DataFrame.from_dict(recs, orient='index')

    # MC Simulation

    def _sample_dimension(
        self, 
        dimension: str
    ) -> float:
        if dimension == 'duration':
            distribution = self.duration_distribution
            mean =         self.duration_mean
            stdev =        self.duration_stdev
            params =       self.duration_params
        elif dimension == 'cost':
            distribution = self.cost_distribution
            mean =         self.cost_mean
            stdev =        self.cost_stdev
            params =       self.cost_params
        else:
            raise ValueError(f'dimension not available')
        val: float
        match distribution:
            case 'fixed':
                val = float(mean)
            case 'uniform':
                val = float(np.random.uniform(params['low'], params['high']))
            case 'exponential':
                val = float(np.random.exponential(mean))
            case 'normal':
                val = float(np.random.normal(mean, stdev))
            case 'log-normal':
                variance = stdev ** 2
                mu = np.log(mean ** 2 / math.sqrt(variance + mean ** 2))
                sigma = math.sqrt(math.log(1 + (variance / mean ** 2)))
                val = float(np.random.lognormal(mu, sigma))
            case 'triangular':
                val = float(np.random.triangular(params['left'], params['mode'], params['right']))
            case 'pert':
                low = params['left']
                high = params['right']
                mode = params['mode']
                mean_pert = (low + 4 * mode + high) / 6
                variance = ((high - low) / 6) ** 2
                alpha = ((mean_pert - low) / (high - low)) * ((mean_pert * (1 - mean_pert)) / variance - 1)
                beta = alpha * (1 - (mean_pert - low) / (high - low))
                val = float(low + (high - low) * np.random.beta(alpha, beta))
            case 'beta':
                val = float(np.random.beta(params['a'], params['b']) * (stdev if stdev else 1) + mean)
            case 'gamma':
                shape = params['shape']
                scale = params.get('scale', mean / shape)
                val = float(np.random.default_rng().gamma(shape, scale))
            case 'weibull':
                k = params['shape']
                scale = params.get('scale', mean / math.gamma(1.0 + 1.0 / k))
                val = float(scale * np.random.default_rng().weibull(k))
            case 'discrete':
                values = np.array(params['values'], dtype=float)
                probs = np.array(params['probs'], dtype=float)
                probs = probs / probs.sum()
                val = float(np.random.default_rng().choice(values, p=probs))
            case _:
                raise ValueError(f'distribution not available, got {distribution}')
        return max(0.0, val)


class ControlAccount:
    """
    Control Account class.
    """

    activity:      Activity
    resource:      Resource
    name:          str
    units:         float
    duration:      float

    direct_cost:   float
    indirect_cost: float
    total_cost:    float

    records:       dict[int, dict]

    __slots__ = (
        'activity',
        'resource',
        'name',
        'units',
        'duration',

        'direct_cost',
        'indirect_cost',
        'total_cost',

        'records',
    )
    _acronym = 'CA'
    __str__  = _common_str
    __repr__ = _common_repr

    def __init__(
        self,
        activity: Activity,
        resource: Resource,
        name: str | None,
        units: float | int | str,
    ):
       
        # Basic
        self.activity = activity
        self.resource = resource 
        self.name =     str(name) if name is not None else f'{self.activity.name}-{self.resource.name}'
        self.units =    float(units)
        self.duration = self.activity.duration

        # Costs
        self.direct_cost =   self._calculate_direct_cost()
        self.indirect_cost = self._calculate_indirect_cost()
        self.total_cost =    self._calculate_total_cost()

        # Monitoring
        self.records: dict[int, dict] = {}
    
    # Costs

    def _calculate_direct_cost(self) -> float:
        if self.resource.resource_type == 'work':
            return self.resource.unit_cost * self.units * self.activity.baseline_duration
        else:
            return self.resource.unit_cost * self.units

    def _calculate_indirect_cost(self) -> float:
        match self.activity.overhead_criterion:
            case 'direct_cost':
                if self.activity.direct_cost > 0.0:
                    return self.activity.indirect_cost * (self.direct_cost / self.activity.direct_cost)
                return self.activity.indirect_cost        
            case _:
                return 0.0
    
    def _calculate_total_cost(self) -> float:
        return self.direct_cost + self.indirect_cost
    
    # Monitoring

    ## EVA
    
    def update_record(
        self, 
        date_key: dt.date | dt.datetime | str | int | float,
        ac: float
    ) -> None:

        # Calendar
        act = self.activity
        cal = act.calendar
        if cal is None:
            raise ValueError()

        # AS, AT
        at_date = cal._parse_date(date_key)

        as_date = act.as_date
        as_days = act.as_days
        
        af_date = act.af_date
        af_days = act.af_days

        if as_date is not None:
            at_days = cal._networkdays(as_date, at_date)
        else:
            at_days = None
            
        # BAC, PD
        bac     = self.total_cost
        pd_days = act.duration
        pd_date = act.ef

        # WS
        if as_date is not None and pd_days > 0:
            if at_date < as_date:
                ws = 0.0
            else:
                nd = cal._networkdays(as_date, at_date)
                ws = max(
                    0.0, 
                    min(nd, pd_days) / pd_days
                )
        else:
            ws = 0.0
    
        # WP
        wp = max(
            (
                rec.get('WP', 0.0)
                for rec_date, rec in self.activity.records.items()
                if rec_date <= date_key
            ),
            default=0.0,
        )
        
        # PV, EV, CV, SV, CPI, SPI, CEACs, TEACs
        pv = bac * ws                   
        ev = bac * wp                   
        cv = ev - ac                    
        sv = ev - pv                    
        cpi = ev / ac if ac != 0.0 else 1.0 
        spi = ev / pv if pv != 0.0 else 1.0
        ceac_cv = bac - cv
        ceac_cpi = bac / cpi if cpi != 0 else math.inf
        teac_spi_days = pd_days / spi if spi != 0 else math.inf
        teac_spi_date = cal._workday(as_date, teac_spi_days) if (as_date is not None and teac_spi_days != math.inf) else pd.NaT
        
        # Add Record
        self.records[date_key] = {
            'AS[Date]':         as_date,
            'AF[Date]':         af_date,
            'PD[Date]':         pd_date,
            'AT[Date]':         at_date,
            'AS[Days]':         as_days,
            'AF[Days]':         af_days,
            'PD[Days]':         pd_days,
            'AT[Days]':         at_days,
            'BAC':              bac,
            'WS':               ws, 
            'WP':               wp, 
            'PV':               pv, 
            'EV':               ev, 
            'AC':               ac,
            'CV':               cv,
            'SV':               sv,
            'CPI':              cpi,
            'SPI':              spi,
            'EAC_CV':           ceac_cv,
            'EAC_CPI':          ceac_cpi,
            'EAC(t)_SPI[Date]': teac_spi_date,
            'EAC(t)_SPI[Days]': teac_spi_days
        }

    def df_eva(self) -> pd.DataFrame:
        recs = self.records
        for date_key in sorted(recs):
            ac = max(
                (rec.get('AC', 0.0) 
                 for rec_date, rec in recs.items()
                 if rec_date <= date_key), 
                 default=0.0
            )
            self.update_record(date_key, ac)
            act = self.activity
            wp = max(
                (rec.get('WP', 0.0) 
                for rec_date, rec in act.records.items() 
                if rec_date <= date_key), 
                default=0.0
            )
            act.update_record(date_key, wp)
            act.project.update_record(date_key)
        return pd.DataFrame.from_dict(recs, orient='index')


class Project:
    """
    Project class.
    """

    name:       str
    activities: dict[str, Activity]
    
    calendar:    Calendar
    start_date:  dt.date
    finish_date: dt.date
    duration:    float

    tracking_freq:  str
    tracking_dates: list[dt.date]

    resources:        dict[str, Resource]
    control_accounts: dict[str, ControlAccount]
        
    direct_cost:   float
    indirect_cost: float
    total_cost:    float

    records: dict[int, dict]
    as_date: dt.date | None
    as_days: int     | None
    af_date: dt.date | None
    af_days: int     | None

    df_mc:                  pd.DataFrame
    df_mc_pmb_project:      pd.DataFrame
    df_mc_pmb_project_cuml: pd.DataFrame

    df_pmb:                 pd.DataFrame
    df_pmb_cuml:            pd.DataFrame
    df_pmb_project:         pd.DataFrame
    df_pmb_project_cuml:    pd.DataFrame

    df_resource_usage:      pd.DataFrame
    df_resource_usage_cuml: pd.DataFrame

    _is_scheduled: bool

    __slots__ = (
        'activities',
        'name',

        'calendar',
        'start_date', 'finish_date', 
        'duration',

        'tracking_freq',
        'tracking_dates',

        'resources',
        'control_accounts',
        
        'direct_cost',
        'indirect_cost',
        'total_cost',

        'records',
        'as_date', 'as_days',
        'af_date', 'af_days',

        'df_mc',
        'df_mc_pmb_project',
        'df_mc_pmb_project_cuml',

        'df_pmb',
        'df_pmb_cuml',
        'df_pmb_project',
        'df_pmb_project_cuml',

        'df_resource_usage',
        'df_resource_usage_cuml',

        '_is_scheduled'
    )
    _acronym = 'P'
    __str__ = _common_str
    __repr__ = _common_repr

    def __init__(
        self,
        activities:    dict[str, Activity] | Iterable[Activity],
        name:          str                                              = 'Project',
        calendar:      None | Calendar                                  = None,
        start_date:    None | dt.datetime | dt.date | int | float | str = None,
        tracking_freq: str                                              = 'D',
    ):

        # Basic
        self.name =       str(name)
        self.calendar =   Calendar()                 if calendar   is None else calendar
        self.start_date = dt.datetime.today().date() if start_date is None else Calendar._parse_date(start_date)
        self._is_scheduled = False

        # Activities
        self.activities = activities if isinstance(activities, dict) else {a.name: a for a in activities}
        self._add_dependencies()
        self._init_activities()

        # Resources
        self.resources: dict[str, Resource] = {}
        self._add_resources()

        # Costs
        self._calculate_costs()
        
        # CAs
        self.control_accounts: dict[str, ControlAccount] = {}
        self._add_controlaccounts()

        # Monitoring
        self.records: dict[int, dict] = {}
        self.as_date = None
        self.as_days = None
        self.af_date = None
        self.af_days = None
        self.tracking_freq = tracking_freq
        self.tracking_dates: list[dt.date] = []
        self._init_tracking_dates()
        self._init_activities_records()
        self._init_controlaccounts_records()
        self._init_project_records()

        # MC Simulation
        self.df_mc = pd.DataFrame()
        self.df_mc_pmb_project = pd.DataFrame()
        self.df_mc_pmb_project_cuml = pd.DataFrame()
        
    # Activities

    def _add_dependencies(self) -> None:
        for a in self.activities.values():
            if a.predecessors:
                for predecessor, rel_type, lag in a.predecessors.values():
                    predecessor.successors[a.name] = (a, rel_type, float(lag))

    def _apply_calendar_to_activities(
            self, 
            force: bool = False
        ) -> None:
        for a in self.activities.values():
            if force or a.calendar is None:
                a.calendar = self.calendar

    def _init_activities(self) -> None:
        acts = self.activities.values()
        for a in acts:

            # Calendar
            if a.calendar is None:
                a.calendar = self.calendar

            cal = a.calendar
            dur = a.duration - 1

            # Scheduling
            if a.es_constraint is False and a.ef_constraint is False:
                es = self.start_date
                while not cal._is_working_day(es):
                    es += dt.timedelta(days=1)
                a.es = es
                a.ef = cal._workday(a.es, +dur)
            elif a.es_constraint is True and a.ef_constraint is False:
                a.ef = cal._workday(a.es, +dur)
            elif a.es_constraint is False and a.ef_constraint is True:
                a.es = cal._workday(a.ef, -dur)
            else:
                a.duration = cal._networkdays(a.es, a.ef)

            if a.ls_constraint is False and a.lf_constraint is False:
                a.ls = a.es
                a.lf = a.ef
            elif a.ls_constraint is True and a.lf_constraint is False:
                a.lf = cal._workday(a.ls, +dur)
            elif a.ls_constraint is False and a.lf_constraint is True:
                a.ls = cal._workday(a.lf, -dur)
            else:
                a.duration = min(
                    a.duration,
                    a.calendar._networkdays(a.ls, a.lf),
                )
                
            # Project
            a.project = self

        self.finish_date = max(a.ef for a in acts if a.ef is not None)
        self.duration = float(self.calendar._networkdays(self.start_date, self.finish_date))

        for a in acts:
            a.slack = a.calendar._networkdays(a.ef, self.finish_date) - 1
            a.critical = a.slack <= 0

    # Resources

    def _add_resources(self) -> None:
        for a in self.activities.values():
            for r, _ in a.resources.values():
                self.resources[r.name] = r

    # Costs

    def _calculate_costs(self) -> None:
        acts = self.activities
        self.direct_cost = sum(a.direct_cost for a in acts.values())
        self.indirect_cost = sum(a.indirect_cost for a in acts.values())
        self.total_cost = self.direct_cost + self.indirect_cost

    # Monitoring

    ## CAs
    def _add_controlaccounts(self) -> None:
        for a in self.activities.values():
            for ca in a.control_accounts.values():
                self.control_accounts[ca.name] = ca

    ## Inits

    def _init_tracking_dates(self) -> None:
        self.tracking_dates = sorted(
            {
                d.date()
                for d in pd.date_range(
                    self.start_date,
                    self.finish_date,
                    freq=self.tracking_freq,
                )
            }
        )

    def _init_activities_records(self) -> None:
        at_dates = self.tracking_dates
        date_keys = [d.year * 10000 + d.month * 100 + d.day for d in at_dates]

        for a in self.activities.values():
            cal =             a.calendar
            as_date_planned = a.es

            bac =     a.total_cost
            pd_days = a.duration
            pd_date = a.ef

            i = 1
            for at_date, date_key in zip(at_dates, date_keys):
                if cal._is_working_day(at_date):
                    i += 1
                at_days = cal._networkdays(as_date_planned, at_date)
                ws = max(0.0, min(1.0, i / pd_days)) if pd_days != 0 else 1.0
                a.records[date_key] = {
                    'AS[Date]':         None,
                    'AF[Date]':         None,
                    'PD[Date]':         pd_date,
                    'AT[Date]':         at_date,
                    'AS[Days]':         None,
                    'AF[Days]':         None,
                    'PD[Days]':         pd_days,
                    'AT[Days]':         at_days,
                    'BAC':              bac,
                    'WS':               ws, 
                    'WP':               0.0, 
                    'PV':               bac * ws, 
                    'EV':               0.0, 
                    'AC':               0.0,
                    'CV':               0.0,
                    'SV':               0.0,
                    'CPI':              1.0,
                    'SPI':              1.0,
                    'EAC_CV':           bac,
                    'EAC_CPI':          bac,
                    'EAC(t)_SPI[Date]': pd_date,
                    'EAC(t)_SPI[Days]': pd_days
                }

    def _init_controlaccounts_records(self) -> None:
        at_dates = self.tracking_dates
        date_keys = [d.year * 10000 + d.month * 100 + d.day for d in at_dates]

        for ca in self.control_accounts.values():
            cal = ca.activity.calendar
            as_date_planned = ca.activity.es

            bac =     ca.total_cost
            pd_days = ca.activity.duration
            pd_date = ca.activity.ef

            i = 1
            for at_date, date_key in zip(at_dates, date_keys):
                if cal._is_working_day(at_date):
                    i += 1
                at_days = cal._networkdays(as_date_planned, at_date)
                ws = max(0.0, min(1.0, i / pd_days)) if pd_days != 0 else 1.0
                ca.records[date_key] = {
                    'AS[Date]':         None,
                    'AF[Date]':         None,
                    'PD[Date]':         pd_date,
                    'AT[Date]':         at_date,
                    'AS[Days]':         None,
                    'AF[Days]':         None,
                    'PD[Days]':         pd_days,
                    'AT[Days]':         at_days,
                    'BAC':              bac,
                    'WS':               ws, 
                    'WP':               0.0, 
                    'PV':               bac * ws, 
                    'EV':               0.0, 
                    'AC':               0.0,
                    'CV':               0.0,
                    'SV':               0.0,
                    'CPI':              1.0,
                    'SPI':              1.0,
                    'EAC_CV':           bac,
                    'EAC_CPI':          bac,
                    'EAC(t)_SPI[Date]': pd_date,
                    'EAC(t)_SPI[Days]': pd_days
                }

    def _init_project_records(self) -> None:
        at_dates = self.tracking_dates
        date_keys = [d.year * 10000 + d.month * 100 + d.day for d in at_dates]

        as_date_planned = self.start_date
        bac =             self.total_cost
        pd_days =         self.duration
        pd_date =         self.finish_date

        for at_date, date_key in zip(at_dates, date_keys):
            at_days = self.calendar._networkdays(as_date_planned, at_date)
                       
            pv = 0.0
            for ca in self.control_accounts.values():
                pv += ca.records[date_key]['PV']

            self.records[date_key] = {
                'AS[Date]':            None,
                'AF[Date]':            None,
                'PD[Date]':            pd_date,
                'AT[Date]':            at_date,
                'AS[Days]':            None,
                'AF[Days]':            None,
                'PD[Days]':            pd_days,
                'AT[Days]':            at_days,
                'BAC':                 bac,
                'WS':                  pv / bac if bac != 0 else 1.0, 
                'WP':                  0.0, 
                'PV':                  pv, 
                'EV':                  0.0, 
                'AC':                  0.0,
                'CV':                  0.0,
                'SV':                  0.0,
                'CPI':                 1.0,
                'SPI':                 1.0,
                'EAC_CV':              bac,
                'EAC_CPI':             bac,
                'EAC(t)_SPI[Date]':    pd_date,
                'EAC(t)_SPI[Days]':    pd_days,
                'ES[Date]':            None,
                'ES[Days]':            None, 
                'SV(t)':               0.0,
                'SPI(t)':              1.0,
                'EAC(t)_SV(t)[Date]':  pd_date,
                'EAC(t)_SV(t)[Days]':  pd_days,
                'EAC(t)_SPI(t)[Date]': pd_date,
                'EAC(t)_SPI(t)[Days]': pd_days,               
            }

    # Schedule

    def _cpm(self) -> None:
        acts = list(self.activities.values())
        if not acts:
            self.finish_date = self.start_date
            self.duration = 0
            return

        processed_activities: set[Activity] = set()

        # Forward Pass (ES, EF)
        while len(processed_activities) < len(acts):
            for a in acts:
                if a in processed_activities:
                    continue
                if not getattr(a, 'es_constraint', False):
                    start_date = self.start_date
                    if a.predecessors:
                        max_start = start_date
                        all_predecessors_processed = True
                        for (predecessor, rel_type, lag) in a.predecessors.values():
                            if predecessor not in processed_activities:
                                all_predecessors_processed = False
                                break
                            if rel_type == 'fs':
                                candidate = a.calendar._workday(predecessor.ef, lag + 1)
                            elif rel_type == 'ff':
                                candidate = a.calendar._workday(predecessor.ef, -a.duration + lag)
                            elif rel_type == 'ss':
                                candidate = a.calendar._workday(predecessor.es, lag)
                            elif rel_type == 'sf':
                                candidate = a.calendar._workday(predecessor.es, -a.duration + lag - 1)
                            else:
                                candidate = start_date
                            max_start = max(max_start, candidate)
                        if all_predecessors_processed:
                            a.es = max(start_date, max_start)
                            if not getattr(a, 'ef_constraint', False):
                                if a.duration == 0:
                                    a.ef = a.es
                                else:
                                    a.ef = a.calendar._workday(a.es, max(0, a.duration - 1))
                            processed_activities.add(a)
                    else:
                        if not getattr(a, 'ef_constraint', False):
                            if a.es is None:
                                a.es = start_date
                            if a.duration == 0:
                                a.ef = a.es
                            else:
                                a.ef = a.calendar._workday(a.es, max(0, a.duration - 1))
                        processed_activities.add(a)
                else:
                    if not getattr(a, 'ef_constraint', False):
                        if a.duration == 0:
                            a.ef = a.es
                        else:
                            a.ef = a.calendar._workday(a.es, max(0, a.duration - 1))
                    processed_activities.add(a)

        # Interlude
        self.finish_date = max(a.ef for a in acts)
        if self.start_date != self.finish_date:
            self.duration = float(self.calendar._networkdays(self.start_date, self.finish_date))
        else:
            self.duration = 0.0
        
        # Backward Pass (LS, LF)
        for a in acts:
            if not a.successors and not getattr(a, 'lf_constraint', False):
                a.lf = self.finish_date
                if a.duration == 0:
                    a.ls = a.ef
                else:
                    a.ls = a.calendar._workday(a.lf, -a.duration + 1)

        processed_activities.clear()
        while len(processed_activities) < len(acts):
            for a in acts:
                if a in processed_activities:
                    continue
                if not getattr(a, 'lf_constraint', False):
                    finish_date = self.finish_date
                    if a.successors:
                        min_finish = finish_date
                        all_successors_processed = True
                        for successor, rel_type, lag in a.successors.values():
                            if successor not in processed_activities:
                                all_successors_processed = False
                                break
                            if rel_type == 'fs':
                                candidate = a.calendar._workday(successor.ls, -lag - 1)
                            elif rel_type == 'ff':
                                candidate = a.calendar._workday(successor.lf, -lag - 1)
                            elif rel_type == 'ss':
                                candidate = a.calendar._workday(successor.ls, successor.duration - a.duration - lag)
                            elif rel_type == 'sf':
                                candidate = a.calendar._workday(successor.lf, successor.duration - a.duration - lag)
                            else:
                                candidate = finish_date
                            min_finish = min(min_finish, candidate) 
                        if all_successors_processed:
                            a.lf = max(a.ef, min_finish)
                            if not getattr(a, 'ls_constraint', False):
                                if a.duration == 0:
                                    a.ls = a.ef
                                else:
                                    a.ls = a.calendar._workday(a.lf, -a.duration + 1)
                            processed_activities.add(a)
                    else:
                        processed_activities.add(a)
                else:
                    if not getattr(a, 'ls_constraint', False):
                        if a.duration == 0:
                            a.ls = a.ef
                        else:
                            a.ls = a.calendar._workday(a.lf, -a.duration + 1)
                    processed_activities.add(a)

        # AS, Slack, Critical
        for a in acts:
            a.as_date = a.es
            a.slack = a.calendar._networkdays(a.es, a.ls) - 1
            a.critical = a.slack <= 0

        # Resource.cost
        resource_total_costs: dict[Resource, float] = {r: 0.0 for r in self.resources.values()}
        for a in acts:
            baseline_duration = a.baseline_duration
            for r, units in a.resources.values():
                if r.resource_type == 'work':
                    resource_total_costs[r] += r.unit_cost * units * baseline_duration
                else:
                    resource_total_costs[r] += r.unit_cost * units
        for r, c in resource_total_costs.items():
            r._total_cost = c

    def schedule(self) -> None:
        self._cpm()
        self._calculate_costs()
        self._init_tracking_dates()
        self._init_activities_records()
        self._init_controlaccounts_records()
        self._init_project_records()
        self._is_scheduled = True

    def _ensure_scheduled(self) -> None:
        if not getattr(self, '_is_scheduled', False):
            raise RuntimeError('Project must be scheduled first. Call project.schedule().')

    # Dataframes

    def df_project(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                'Name':          [self.name],
                'Start Date':    [self.start_date],
                'Finish Date':   [self.finish_date],
                'Duration':      [self.duration],
                'Direct Cost':   [self.direct_cost],
                'Indirect Cost': [self.indirect_cost],
                'Total Cost':    [self.total_cost],
            }
        )
    
    def df_activities(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    'Name':                  a.name,
                    'Predecessors': ', '.join(
                        f'{p.name}({r})+{l}'
                        for p, r, l in (a.predecessors or {}).values()
                    ),
                    # 'Successors': ', '.join(
                    #     f'{p.name}({r})+{l}'
                    #     for p, r, l in (a.successors or {}).values()
                    # ),
                    'Baseline Resources': ', '.join(
                        f'{p.name}({r})'
                        for p, r in (a.baseline_resources or {}).values()
                    ),
                    'Baseline Duration':     a.baseline_duration,
                    'Effort Driven': a.effort_driven,
                    'Resources': ', '.join(
                        f'{p.name}({r})'
                        for p, r in (a.resources or {}).values()
                    ),
                    'Calendar':              a.calendar.name,
                    'Duration':              a.duration,
                    'Direct Cost':           a.direct_cost,
                    'Indirect Cost':         a.indirect_cost,
                    'Total Cost':            a.total_cost,
                    'ES':                    a.es,
                    'EF':                    a.ef,
                    'LS':                    a.ls,
                    'LF':                    a.lf,
                    'ES Constrained':        a.es_constraint,
                    'EF Constrained':        a.ef_constraint,
                    'LS Constrained':        a.ls_constraint,
                    'LF Constrained':        a.lf_constraint,
                    'Slack':                 a.slack,
                    'Critical':              a.critical,
                    'Duration Distribution': a.duration_distribution,
                    'Duration Mean':         a.duration_mean,
                    'Duration Stdev':        a.duration_stdev,
                    'Duration Params':       a.duration_params,
                    'Cost Distribution':     a.cost_distribution,
                    'Cost Mean':             a.cost_mean,
                    'Cost Stdev':            a.cost_stdev,
                    'Cost Params':           a.cost_params,
                }
                for a in self.activities.values()
            ]
        )

    def df_resources(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    'Name':         r.name,
                    'Type':         r.resource_type,
                    'Availability': r.availability,
                    'Unit Cost':    r.unit_cost,
                    'Total Cost':   r.total_cost
                }
                for r in self.resources.values()
            ]
        ).sort_values('Name', kind='stable').reset_index(drop=True)

    def df_controlaccounts(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    'Name':          ca.name,
                    'Activity':      ca.activity.name,
                    'Resource':      ca.resource.name,
                    'Units':         ca.units,
                    'Duration':      ca.duration,
                    'Direct Cost':   ca.direct_cost,
                    'Indirect Cost': ca.indirect_cost,
                    'Total Cost':    ca.total_cost,
                }
                for ca in self.control_accounts.values()
            ]
        ).sort_values('Name', kind='stable').reset_index(drop=True)

    # Performance Measurement Baseline

    def _pmb(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        activities = list(self.activities.values())

        dates = self.tracking_dates
        num_dates = len(dates)

        a_names = [a.name for a in activities]
        num_activities = len(a_names)

        pmb_array = np.zeros((num_activities, num_dates), dtype=float)
        a_name_to_index = {a.name: i for i, a in enumerate(activities)}
        date_to_index = {date: i for i, date in enumerate(dates)}

        for a in activities:
            working_days = [
                target_date.date()
                for target_date in pd.date_range(a.es, a.ef, freq='D')
                if a.calendar._is_working_day(target_date.date())
            ]
            daily_cost = a.total_cost / len(working_days) if working_days else 0.0

            a_idx = a_name_to_index[a.name]
            for day in working_days:
                idx = date_to_index.get(day)
                if idx is not None:
                    pmb_array[a_idx, idx] = daily_cost

        pmb_cuml = np.cumsum(pmb_array, axis=1)
        pmb_project = np.sum(pmb_array, axis=0)
        pmb_project_cuml = np.cumsum(pmb_project)

        df_pmb      = pd.DataFrame(pmb_array, index=a_names, columns=dates).T
        df_pmb_cuml = pd.DataFrame(pmb_cuml,  index=a_names, columns=dates)

        df_pmb_project      = pd.Series(pmb_project,      index=dates, name='PV')
        df_pmb_project_cuml = pd.Series(pmb_project_cuml, index=dates, name='PV')
       
        return df_pmb, df_pmb_cuml, df_pmb_project, df_pmb_project_cuml

    def pmb(self) -> None:
        df_pmb, df_pmb_cuml, df_pmb_project, df_pmb_project_cuml = (
            self._pmb()
        )
        self.df_pmb =              df_pmb
        self.df_pmb_cuml =         df_pmb_cuml
        self.df_pmb_project =      df_pmb_project
        self.df_pmb_project_cuml = df_pmb_project_cuml
    
    def _resource_usage(self):
        activities = list(self.activities.values())
        resources  = list(self.resources.values())

        dates = self.tracking_dates
        num_dates = len(dates)

        r_names = [r.name for r in resources]
        num_resources = len(r_names)

        usage_array = np.zeros((num_resources, num_dates), dtype=float)

        r_name_to_index = {resource.name: i for i, resource in enumerate(resources)}
        date_to_index = {date: i for i, date in enumerate(dates)}
        for a in activities:
            working_days = [
                date.date()
                for date in pd.date_range(a.es, a.ef, freq='D')
                if a.calendar._is_working_day(date.date())
            ]
            if not working_days:
                continue
            for res_name, (r, units) in a.resources.items():
                res_idx = r_name_to_index.get(res_name)
                if res_idx is None:
                    continue
                daily_use = units
                for day in working_days:
                    day_idx = date_to_index.get(day)
                    if day_idx is not None:
                        usage_array[res_idx, day_idx] += daily_use
        usage_cuml = np.cumsum(usage_array, axis=1)
        df_resource_usage = pd.DataFrame(usage_array, index=r_names, columns=dates)
        df_resource_usage_cuml = pd.DataFrame(
            usage_cuml,
            index=r_names,
            columns=dates,
        )
        return df_resource_usage, df_resource_usage_cuml

    def resource_usage(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        df_resource_usage, df_resource_usage_cuml = self._resource_usage()
        self.df_resource_usage = df_resource_usage.T
        self.df_resource_usage_cuml =df_resource_usage_cuml.T

    # Monitoring

    def update_record(
        self,
        date_key: dt.date | dt.datetime | str | int | float,
    ) -> None:
        
        acts_values = self.activities.values()
        # Calendar
        cal = self.calendar

        # AS, AT
        at_date = cal._parse_date(date_key)
        
        as_dates = [a.as_date for a in acts_values if a.as_date is not None]
        as_date = min(as_dates) if as_dates else None
        as_days = None if as_date is None else cal._networkdays(as_date, self.start_date)-1
        
        af_dates = [a.af_date for a in acts_values if a.af_date is not None]
        af_date = max(af_dates) if af_dates else None
        af_days = None if af_date is None else cal._networkdays(as_date, af_date)
        
        if as_date is not None:
            at_days = cal._networkdays(as_date, at_date)
        else:
            at_days = None

        # BAC, PD
        bac =     self.total_cost
        pd_days = self.duration
        pd_date = self.finish_date

        # PV, EV, AC
        pv = 0.0
        ev = 0.0
        ac = 0.0
        for a in acts_values:
            rec = a.records[date_key]
            pv += rec['PV']
            ev += rec['EV']
            ac += rec['AC']

        # WS, WP, CV, SV, CPI, SPI, CEACs, TEACs
        ws = pv / bac                   
        wp = ev / bac                                               
        cv = ev - ac                                                
        sv = ev - pv                                                
        cpi = ev / ac if ac != 0.0 else 1.0                             
        spi = ev / pv if pv != 0.0 else 1.0                             
        ceac_cv = bac - cv
        ceac_cpi = bac / cpi if cpi != 0 else math.inf
        teac_spi_days = pd_days / spi if spi != 0 else math.inf
        teac_spi_date = cal._workday(as_date, teac_spi_days) if (as_date is not None and teac_spi_days != math.inf) else pd.NaT

        # ESs, SV(t), SPI(t)
        es_days = 0.0
        
        if not hasattr(self, 'df_pmb_project_cuml') or getattr(self, 'df_pmb_project_cuml') is None or len(self.df_pmb_project_cuml) == 0:
            self.pmb()
        ppmb_cuml_ws = self.df_pmb_project_cuml / bac if bac > 0 else self.df_pmb_project_cuml * 0
        if wp <= 0:
            es_days = 0.0
            es_date = as_date
        elif wp >= 1:
            es_days = pd_days
            es_date = pd_date
        else:
            c = sum(1 for val in ppmb_cuml_ws.values if wp > val)
            es_date = ppmb_cuml_ws.index[c]
            es_days = cal._networkdays(as_date, es_date)

        sv_t =            es_days - at_days
        spi_t =           es_days / at_days if at_days != 0.0 else 1.0
        teac_sv_t_days =  pd_days - sv_t
        teac_sv_t_date =  cal._workday(as_date, teac_sv_t_days) if teac_sv_t_days != math.inf else math.inf
        teac_spi_t_days = pd_days / spi_t if spi_t != 0 else math.inf
        teac_spi_t_date = cal._workday(as_date, teac_spi_t_days) if (as_date is not None and teac_spi_t_days != math.inf) else pd.NaT

        # Add Record
        self.records[date_key] = {
            'AS[Date]':            as_date,
            'AF[Date]':            af_date,
            'PD[Date]':            pd_date,
            'AT[Date]':            at_date,
            'AS[Days]':            as_days,
            'AF[Days]':            af_days,
            'PD[Days]':            pd_days,
            'AT[Days]':            at_days,
            'BAC':                 bac,
            'WS':                  ws, 
            'WP':                  wp, 
            'PV':                  pv, 
            'EV':                  ev, 
            'AC':                  ac,
            'CV':                  cv,
            'SV':                  sv,
            'CPI':                 cpi,
            'SPI':                 spi,
            'EAC_CV':              ceac_cv,
            'EAC_CPI':             ceac_cpi,
            'EAC(t)_SPI[Days]':    teac_spi_days,
            'EAC(t)_SPI[Date]':    teac_spi_date,
            'ES[Days]':            es_days,
            'ES[Date]':            es_date,
            'SV(t)':               sv_t,
            'SPI(t)':              spi_t,
            'EAC(t)_SV(t)[Days]':  teac_sv_t_days,
            'EAC(t)_SV(t)[Date]':  teac_sv_t_date,
            'EAC(t)_SPI(t)[Days]': teac_spi_t_days,
            'EAC(t)_SPI(t)[Date]': teac_spi_t_date,
        }

    def df_eva(
        self,
        progress_bar = None
    ) -> pd.DataFrame:
        recs = self.records
        date_keys = sorted(recs)
        N = len(date_keys)

        for i, date_key in enumerate(date_keys, start=1):
            for a in self.activities.values():
                wp = max(
                    (
                        rec.get('WP', 0.0)
                        for rec_date, rec in a.records.items()
                        if rec_date <= date_key
                    ),
                    default=0.0
                )
                for control_account in a.control_accounts.values():
                    ac = max(
                        (
                            rec.get('AC', 0.0)
                            for rec_date, rec in control_account.records.items()
                            if rec_date <= date_key
                        ),
                        default=0.0
                    )
                    control_account.update_record(date_key, ac)
                a.update_record(date_key, wp)
            if progress_bar is not None:
                wpt = int(100 * (i / N))
                progress_bar.progress(wpt, text=f'Progress: {i}/{N}')
            self.update_record(date_key)
        return pd.DataFrame.from_dict(recs, orient='index')
    
    # MC Simulation

    def mc(
        self,
        n_simulations: int  = 1,
        track_pmb:     bool = False,
        progress_bar        = None, 
        ) -> None:

        baseline_project_values = {
            'finish_date':    getattr(self, 'finish_date', None),
            'duration':       getattr(self, 'duration', None),
            'direct_cost':    getattr(self, 'direct_cost', None),
            'indirect_cost':  getattr(self, 'indirect_cost', None),
            'total_cost':     getattr(self, 'total_cost', None),
            'tracking_dates': list(getattr(self, 'tracking_dates', [])),
        }

        baseline_activities_values = {
            name: {
                'duration':      a.duration,
                'direct_cost':   a.direct_cost,
                'indirect_cost': a.indirect_cost,
                'total_cost':    a.total_cost,
                'es':            getattr(a, 'es', None),
                'ef':            getattr(a, 'ef', None),
                'ls':            getattr(a, 'ls', None),
                'lf':            getattr(a, 'lf', None),
                'slack':         getattr(a, 'slack', None),
                'critical':      getattr(a, 'critical', None),
                'as_date':       getattr(a, 'as_date', None),
            }
            for name, a in self.activities.items()
        }

        durations =                 []
        finish_dates =              []
        direct_costs =              []
        indirect_costs =            []
        total_costs =               []
        pmb_project_scenarios =     []
        pmb_project_cum_scenarios = []

        def _restore_baseline():
            self.finish_date =    baseline_project_values['finish_date']
            self.duration =       baseline_project_values['duration']
            self.direct_cost =    baseline_project_values['direct_cost']
            self.indirect_cost =  baseline_project_values['indirect_cost']
            self.total_cost =     baseline_project_values['total_cost']
            self.tracking_dates = list(baseline_project_values['tracking_dates'])
            for name, attrs in baseline_activities_values.items():
                a = self.activities[name]
                for attr, value in attrs.items():
                    setattr(a, attr, value)

        for i in range(n_simulations):
            _restore_baseline()
            for a in self.activities.values():
                a.duration =      a._sample_dimension('duration')
                a.direct_cost =   a._sample_dimension('cost')
                a.indirect_cost = a.duration * a.overhead_rate
                a.total_cost =    a.direct_cost + a.indirect_cost
            self._cpm()
            self._calculate_costs()

            if track_pmb:
                self._init_tracking_dates()

            durations.append(      self.duration)
            finish_dates.append(  self.finish_date)
            direct_costs.append(  self.direct_cost)
            indirect_costs.append(self.indirect_cost)
            total_costs.append(   self.total_cost)

            if track_pmb:
                _, _, pmb_project, pmb_project_cuml = self._pmb()
                pmb_project_scenarios.append(pmb_project.to_numpy())
                pmb_project_cum_scenarios.append(pmb_project_cuml.to_numpy())

            if progress_bar is not None:
                wpt = int(100 * (i + 1) / n_simulations)
                progress_bar.progress(wpt, text=f'Progress: {i+1}/{n_simulations}')

        self.df_mc = pd.DataFrame(
            {
                'Duration':      durations,
                'Finish Date':   finish_dates,
                'Direct Cost':   direct_costs,
                'Indirect Cost': indirect_costs,
                'Total Cost':    total_costs,
            }
        )

        if track_pmb:
            def _aggregate_scenarios(scenarios) -> pd.DataFrame:
                max_len = max(len(arr) for arr in scenarios)
                data = np.full((len(scenarios), max_len), np.nan, dtype=float)
                for i, arr in enumerate(scenarios):
                    data[i, : len(arr)] = arr
                return pd.DataFrame(
                    {
                        'min':  np.nanmin(data, axis=0),
                        'p05':  np.nanpercentile(data, 5, axis=0),
                        'p25':  np.nanpercentile(data, 25, axis=0),
                        'p50':  np.nanpercentile(data, 50, axis=0),
                        'mean': np.nanmean(data, axis=0),
                        'p75':  np.nanpercentile(data, 75, axis=0),
                        'p95':  np.nanpercentile(data, 95, axis=0),
                        'max':  np.nanmax(data, axis=0),
                    }
                )
            self.df_mc_pmb_project =      _aggregate_scenarios(pmb_project_scenarios)
            self.df_mc_pmb_project_cuml = _aggregate_scenarios(pmb_project_cum_scenarios)
        else:
            self.df_mc_pmb_project =      pd.DataFrame()
            self.df_mc_pmb_project_cuml = pd.DataFrame()


class Portfolio:
    """
    Portfolio class.
    """

    name:     str
    projects: dict[str, Project]

    __slots__ = (
        'name',
        'projects',
    )

    _acronym = 'PF'
    __str__  = _common_str
    __repr__ = _common_repr

    def __init__(
        self,
        projects: dict[str, Project] | Iterable[Project],
        name:     str = 'Portfolio',
    ) -> None:
        self.name     = str(name)
        self.projects = {p.name: p for p in projects} if not isinstance(projects, dict) else projects

    def df_projects(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    'Name':               p.name,
                    'Start Date':         p.start_date,
                    'Finish Date':        p.finish_date,
                    'Tracking Frequency': p.tracking_freq,
                    'Duration':           p.duration,
                    'Direct Cost':        p.direct_cost,
                    'Indirect Cost':      p.indirect_cost,
                    'Total Cost':         p.total_cost,
                }
                for p in self.projects.values()
            ]
        )

    def df_eva(self) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        keys:   list[str]          = []

        for p in self.projects.values():
            frames.append(p.df_eva())
            keys.append(p.name)

        df = pd.concat(
            frames, 
            keys=keys, 
            names=['Project Name', 'AT[Date]']
        ).reset_index(level='Project Name')

        completed = (
            df.loc[df['WP'] == 1]
            .groupby('Project Name')
            .agg(
                AC_AD=  ('AC',       'max'),
                AD_date=('AT[Date]', 'max'),
                AD_days=('AT[Days]', 'max'),
            )
            .rename(columns={
                'AC_AD':   'AC(AD[Days])',
                'AD_date': 'AD[Date]',
                'AD_days': 'AD[Days]',
            })
        )
        df = df.merge(completed, on='Project Name', how='left')
        
        return df
    
    def init_aip(
        self,
        interpolate:      bool       = True,
        interpolate_pct:  float      = 0.01,
        scale:            bool       = True,
        wp_lb:            float      = 0.01,
        wp_ub:            float      = 0.99,
        target:           str        = 'cost',       
        method:           str        = 'direct',
        eval_metric:      str        = 'mean_absolute_error',
        loss:             str        = 'absolute_error',
        feature_selector: str        = 'SequentialFeatureSelector',
        X_cols:           list[str]  = ['BAC', 'AT[Days]', 'WS', 'WP', 'AC', 'ES[Days]'],
        model:            str        = 'LinearRegression',
        progress_bar = None,
    ):
        
        # Data Collection
        df0 = self.df_eva().copy()

        # Interpolation
        if interpolate:
            df1 = pd.DataFrame(columns=df0.columns)
            n = int(round(1 / interpolate_pct))
            wpts = np.arange(n + 1) / n

            for project_name in df0['Project Name'].unique():
                df_temp = df0[df0['Project Name'] == project_name].reset_index(drop=True)

                as_date = df_temp['AS[Date]'].max()
                af_date = df_temp['AF[Date]'].max()
                pd_date = df_temp['PD[Date]'].max()

                as_days = df_temp['AS[Days]'].max()
                af_days = df_temp['AF[Days]'].max()
                pd_days = df_temp['PD[Days]'].max()

                bac = df_temp['BAC'].max()
                ac_ad_days = df_temp['AC(AD[Days])'].max()
                ad_date = df_temp['AD[Date]'].max()
                ad_days = df_temp['AD[Days]'].max()

                seed_row = pd.DataFrame(
                    {
                        'Project Name':        project_name,
                        'AS[Date]':            as_date,
                        'AF[Date]':            af_date,
                        'PD[Date]':            pd_date,
                        'AT[Date]':            as_date,
                        'AS[Days]':            as_days,
                        'AF[Days]':            af_days,
                        'PD[Days]':            pd_days,
                        'AT[Days]':            0.0,
                        'BAC':                 bac,
                        'WS':                  0.0,
                        'WP':                  0.0,
                        'PV':                  0.0,
                        'EV':                  0.0,
                        'AC':                  0.0,
                        'CV':                  0.0,
                        'SV':                  0.0,
                        'CPI':                 1.0,
                        'SPI':                 1.0,
                        'SPI(t)':              1.0,
                        'EAC_CV':              bac,
                        'EAC_CPI':             bac,
                        'EAC(t)_SPI[Date]':    pd_date,
                        'EAC(t)_SPI[Days]':    pd_days,
                        'ES[Date]':            as_date,
                        'ES[Days]':            0.0,
                        'SV(t)':               0.0,
                        'EAC(t)_SV(t)[Date]':  pd_date,
                        'EAC(t)_SV(t)[Days]':  pd_days,
                        'EAC(t)_SPI(t)[Date]': pd_date,
                        'EAC(t)_SPI(t)[Days]': pd_days,
                        'AC(AD[Days])':        ac_ad_days,
                        'AD[Date]':            ad_date,
                        'AD[Days]':            ad_days
                    },
                    index=[0],
                )
                df_temp = pd.concat([seed_row, df_temp], ignore_index=True)

                # ES
                PVs = df_temp['PV'].to_numpy()
                TPs = df_temp['AT[Days]'].to_numpy()

                for wpt in wpts:
                    if wpt != 0:
                        k = sum(1 for wp in df_temp['WP'] if wpt >= wp)
                        if k < len(df_temp['WP']):
                            denom_wp = (df_temp['WP'][k] - df_temp['WP'][k - 1])
                            incr = (wpt - df_temp['WP'][k - 1]) / denom_wp

                            at_days_itp = (
                                df_temp['AT[Days]'][k - 1]
                                + (df_temp['AT[Days]'][k] - df_temp['AT[Days]'][k - 1]) * incr
                            )
                            pv_itp = (
                                df_temp['PV'][k - 1]
                                + (df_temp['PV'][k] - df_temp['PV'][k - 1]) * incr
                            )
                            ac_itp = (
                                df_temp['AC'][k - 1]
                                + (df_temp['AC'][k] - df_temp['AC'][k - 1]) * incr
                            )
                        else:
                            at_days_itp = df_temp['AT[Days]'][k - 1]
                            pv_itp = df_temp['PV'][k - 1]
                            ac_itp = df_temp['AC'][k - 1]
                    else:
                        at_days_itp = 0
                        pv_itp = 0
                        ac_itp = 0

                    ev_itp = wpt * bac
                    cv = ev_itp - ac_itp
                    sv = ev_itp - pv_itp
                    cpi = ev_itp / ac_itp if ac_itp != 0.0 else 1.0                             
                    spi = ev_itp / pv_itp if pv_itp != 0.0 else 1.0                             
                    ceac_cv = bac - cv
                    ceac_cpi = bac / cpi if cpi != 0 else math.inf
                    teac_spi_days = pd_days / spi if spi != 0 else math.inf
                    # teac_spi_date = Calendar._workday(AS_date, teac_spi_days) if (AS_date is not None and teac_spi_days != math.inf) else pd.NaT
                    
                    # ESs, SV(t), SPI(t)
                    c = sum(1 for pv in PVs if ev_itp >= pv)
                    if c < len(PVs):
                        if PVs[c] == max(PVs):
                            AT_next = pd_days
                        else:
                            AT_next = TPs[c]
                        es_days = TPs[c - 1] + (wpt*bac - PVs[c - 1]) / (PVs[c] - PVs[c - 1]) * (AT_next - TPs[c - 1])
                    elif c == len(PVs):
                        es_days = pd_days
                    sv_t = es_days - at_days_itp
                    spi_t = es_days / at_days_itp if at_days_itp != 0.0 else 1.0
                    teac_sv_t_days = pd_days - sv_t
                    # teac_sv_t_date = Calendar._workday(as_date, teac_sv_t_days) if teac_sv_t_days != math.inf else math.inf
                    teac_spi_t_days = pd_days / spi_t if spi_t != 0 else math.inf
                    # teac_spi_t_date = Calendar._workday(as_date, teac_spi_t_days) if (as_date is not None and teac_spi_t_days != math.inf) else pd.NaT

                    new_row = pd.DataFrame(
                        {
                            'Project Name':        project_name,
                            'AS[Date]':            as_date,
                            'AF[Date]':            af_date,
                            'PD[Date]':            pd_date,
                            'AT[Date]':            None,
                            'AS[Days]':            as_days,
                            'AF[Days]':            af_days,
                            'PD[Days]':            pd_days,
                            'AT[Days]':            at_days_itp,
                            'BAC':                 bac,
                            'WS':                  pv_itp / bac,
                            'WP':                  wpt,
                            'PV':                  pv_itp,
                            'EV':                  ev_itp,
                            'AC':                  ac_itp,
                            'CV':                  cv,
                            'SV':                  sv,
                            'CPI':                 cpi,
                            'SPI':                 spi,
                            'SPI(t)':              spi_t,
                            'EAC_CV':              ceac_cv,
                            'EAC_CPI':             ceac_cpi,
                            'EAC(t)_SPI[Date]':    None,
                            'EAC(t)_SPI[Days]':    teac_spi_days,
                            'ES[Date]':            None,
                            'ES[Days]':            es_days,
                            'SV(t)':               sv_t,
                            'EAC(t)_SV(t)[Date]':  None,
                            'EAC(t)_SV(t)[Days]':  teac_sv_t_days,
                            'EAC(t)_SPI(t)[Date]': None,
                            'EAC(t)_SPI(t)[Days]': teac_spi_t_days,
                            'AC(AD[Days])':        ac_ad_days,
                            'AD[Date]':            ad_date,
                            'AD[Days]':            ad_days
                        },
                        index=[0],
                    )
                    df1 = pd.concat([df1, new_row], axis=0, ignore_index=True)
            df1 = df1.reset_index(drop=True)
        else:
            df1 = df0.copy()
            wpts = sorted(df1['WP'].unique().tolist()) if 'WP' in df1.columns else [0.0]

        # Scaling
        df2 = df1.copy()
        if scale == True:
            # Cost-related
            df2['EV']  =          df2['EV']           / df2['BAC']
            df2['PV']  =          df2['PV']           / df2['BAC']
            df2['AC']  =          df2['AC']           / df2['BAC']
            df2['CV']  =          df2['CV']           / df2['BAC']
            df2['AC(AD[Days])'] = df2['AC(AD[Days])'] / df2['BAC']
            df2['EAC_CV'] =       df2['EAC_CV']       / df2['BAC']
            df2['EAC_CPI'] =      df2['EAC_CPI']      / df2['BAC']
            df2['BAC'] =          1.0
            # Time-related
            df2['AS[Days]'] =            df2['AS[Days]']            / df2['PD[Days]']
            df2['AD[Days]'] =            df2['AD[Days]']            / df2['PD[Days]']
            df2['AT[Days]'] =            df2['AT[Days]']            / df2['PD[Days]']
            df2['ES[Days]'] =            df2['ES[Days]']            / df2['PD[Days]']
            df2['SV(t)']    =            df2['SV(t)']               / df2['PD[Days]']
            df2['EAC(t)_SPI[Days]'] =    df2['EAC(t)_SPI[Days]']    / df2['PD[Days]']
            df2['EAC(t)_SV(t)[Days]'] =  df2['EAC(t)_SV(t)[Days]']  / df2['PD[Days]']
            df2['EAC(t)_SPI(t)[Days]'] = df2['EAC(t)_SPI(t)[Days]'] / df2['PD[Days]']
            df2['PD[Days]'] =            1.0

        # Indirect Regression Targets
        df3 = df2.copy()
        df3['cPF_real'] = 1.0
        df3['sPF_real'] = 1.0

        denom_c = (df3['AC(AD[Days])'].astype(float) - df3['AC'].astype(float)).replace(0, np.nan)
        numer_c = (df3['BAC'].astype(float)          - df3['EV'].astype(float))
        df3['cPF_real'] = (numer_c / denom_c).replace(0, np.nan)

        denom_s = (df3['AD[Days]'].astype(float) - df3['AT[Days]'].astype(float)).replace(0, np.nan)
        numer_s = (df3['PD[Days]'].astype(float) - df3['ES[Days]'].astype(float))
        df3['sPF_real'] = (numer_s / denom_s).replace(0, np.nan)

        # Filter
        df4 = df3.copy()
        df4 = df4.loc[(df4['WP'] >= wp_lb) & (df4['WP'] <= wp_ub)].reset_index(drop=True)
        wpts_filtered = [wpt for wpt in wpts if wpt >= wp_lb and wpt <= wp_ub]

        # X, y
        X = df4[list(X_cols)].copy()
        if target == 'cost':
            if method == 'direct':
                y_true_col = 'AC(AD[Days])'
            elif method == 'indirect':
                y_true_col = 'cPF_real'
        elif target == 'time':
            if method == 'direct':
                y_true_col = 'AD[Days]'
            elif method == 'indirect':
                y_true_col = 'sPF_real'
        y = df4[y_true_col].copy()
        codes = df4['Project Name'].copy()
        y_pred_col = model + '_' + target + '_' + method 

        # df_out
        out_cols = ['Project Name', 'AC(AD[Days])', 'AD[Days]', 'cPF_real', 'sPF_real'] + X_cols 
        df_out = df4[out_cols].copy()
        
        # dfr_x
        dfr_model = pd.DataFrame(columns=[
            'Model',
            'Method',
            'MAE',
            'A^IQR',
            'A^IDR'
        ])

        dfr_wp = pd.DataFrame(columns=[
            'WP',
            'MAE',
        ])
        dfr_wp['WP'] = wpts_filtered 

        dfr_project = pd.DataFrame(columns=[
            'Project Name',
            'Model',
            'Method',
            'MAE',
        ])

        # Parameters
        eval_metric_FS = 'neg_' + eval_metric
        loss = loss

        from sklearn.metrics import mean_absolute_error
        
        from sklearn.model_selection import GridSearchCV
        from sklearn.model_selection import LeaveOneGroupOut
        
        if feature_selector == 'SequentialFeatureSelector':
            from sklearn.feature_selection import SequentialFeatureSelector
            feature_selector_cls = SequentialFeatureSelector
        
        if model == 'LinearRegression':
            from sklearn.linear_model import LinearRegression
            model_cls = LinearRegression(fit_intercept=True, n_jobs=-1)
            HPs = {}
        elif model == 'MLPRegressor':
            from sklearn.neural_network import MLPRegressor
            model_cls = MLPRegressor(
                hidden_layer_sizes=(5,5),
                activation='relu',
                learning_rate='adaptive',
                solver='adam',
                alpha=1e-4,
                batch_size='auto',
                learning_rate_init=1e-3,
                power_t=0.25,
                max_iter=100,
                shuffle=True,
                tol=1e-4,
                warm_start=False,
                momentum=0.9,
                nesterovs_momentum=True,
                early_stopping=True,
                validation_fraction=.1,
                beta_1=0.9,
                beta_2=0.999,
                epsilon=1e-08,
                n_iter_no_change=10,
                max_fun=15000,
                verbose=0,
                random_state=0,
            )
            HPs = {}
        
        # Feature Selection
        def SFS(
            X_train, 
            y_train, 
            codes_train, 
            feature_selector_cls, 
            model_cls,
            eval_metric_FS,
        ) -> list[str]:
            cv = list(LeaveOneGroupOut().split(X_train, y_train, codes_train))
            selector = feature_selector_cls(
                model_cls,
                n_features_to_select='auto',
                tol=1e-6,
                direction='forward',
                scoring=eval_metric_FS,
                cv=cv,
                n_jobs=-1,
            )
            selector = selector.fit(X_train, y_train)
            best = list(selector.get_feature_names_out())
            return best

        # HPT
        def HPT(
            X_train, 
            y_train, 
            best,
            codes_train, 
            model_cls,
            HPs,
            eval_metric_FS
        ):
            cv = list(LeaveOneGroupOut().split(X_train[best], y_train, codes_train))
            if HPs != {}:
                grid_search_CV = GridSearchCV(
                    model_cls,
                    param_grid=HPs,
                    scoring=eval_metric_FS,
                    cv=cv,
                    refit=True,
                    n_jobs=-1,
                )
                grid_search_CV.fit(
                    X_train[best],
                    y_train,
                    groups=codes_train
                )
                best_model = grid_search_CV.best_estimator_
            else:
                best_model = model_cls.fit(
                    X_train[best],
                    y_train
                )
            return best_model
        
        # Score
        def scores(
            wpts_filtered, 
            df_out, 
            y_true_col,
            y_pred_col,
            dfr_wp,
            dfr_model,
            dfr_project
        ):
            MAEs = []
            LBs = []
            Q1s = []
            Ms = []
            Q3s = []
            UBs = []
            for wpt in wpts_filtered:
                df_temp = df_out.loc[df_out.WP == wpt]
                MAEs.append( mean_absolute_error(    df_temp[y_true_col], df_temp[y_pred_col]))
                LBs.append(np.percentile(df_temp['E_' + y_pred_col], 10))
                Q1s.append(np.percentile(df_temp['E_' + y_pred_col], 25))
                Ms.append( np.percentile(df_temp['E_' + y_pred_col], 50))
                Q3s.append(np.percentile(df_temp['E_' + y_pred_col], 75))
                UBs.append(np.percentile(df_temp['E_' + y_pred_col], 90))

            dfr_wp['MAE_'  + y_pred_col] = MAEs
            dfr_wp['LB_'   + y_pred_col] = LBs
            dfr_wp['Q1_'   + y_pred_col] = Q1s
            dfr_wp['M_'    + y_pred_col] = Ms
            dfr_wp['Q3_'   + y_pred_col] = Q3s
            dfr_wp['UB_'   + y_pred_col] = UBs

            new_row = {
                'Model':  model,
                'Method': method,
                'MAE':    mean_absolute_error(    df_out[y_true_col], df_out[y_pred_col]),
                'A^IQR':  abs(np.trapz(dfr_wp['Q1_' + y_pred_col], axis=0)) + abs(np.trapz(dfr_wp['Q3_' + y_pred_col], axis=0)),
                'A^IDR':  abs(np.trapz(dfr_wp['LB_' + y_pred_col], axis=0)) + abs(np.trapz(dfr_wp['UB_' + y_pred_col], axis=0)),
            }
            dfr_model = pd.concat([dfr_model, pd.DataFrame([new_row])], ignore_index=True)

            rows = []
            for proj, g in df_out.groupby('Project Name'):
                rows.append({
                    'Model': model,
                    'Method': method,
                    'Project Name': proj,
                    'MAE':  mean_absolute_error(    g[y_true_col], g[y_pred_col]),
                })
            dfr_project = pd.DataFrame(rows)
            
            return dfr_model, dfr_wp, dfr_project

        # Run
        def run(
            X,
            y,
            codes,
            feature_selector_cls,
            model_cls,
            eval_metric_FS,
            HPs,
            df_out,
            dfr_model,
            dfr_wp,
            dfr_project,
            y_true_col,
            y_pred_col,
            wpts_filtered,
            progress_bar,
        ):
            # Model
            df_out[y_pred_col] = np.ones(len(df_out))
            n_folds = codes.nunique()

            it = 0
            for train_Index, test_Index in LeaveOneGroupOut().split(X, y, codes):
              
                # Train-Test Split
                X_train = X.iloc[train_Index]
                y_train = y.iloc[train_Index]
                codes_train = codes.iloc[train_Index]

                # Feature Selection          
                best = SFS(
                    X_train, 
                    y_train, 
                    codes_train, 
                    feature_selector_cls, 
                    model_cls,
                    eval_metric_FS,
                )

                # GridSearchCV
                best_model = HPT(
                    X_train, 
                    y_train, 
                    best,
                    codes_train, 
                    model_cls,
                    HPs,
                    eval_metric_FS
                )
                y_preds = np.array(best_model.predict(X[best]))
                for i in test_Index:
                    df_out.loc[i, y_pred_col] = y_preds[i]
                df_out['E_' + y_pred_col] = df_out[y_true_col] - df_out[y_pred_col]

                if progress_bar is not None:
                    wpt = int(100 * (it + 1) / n_folds)
                    progress_bar.progress(wpt, text=f'Progress: {it+1}/{n_folds}')
                    it += 1

            # Scores
            dfr_model, dfr_wp, dfr_project = scores(
                wpts_filtered, 
                df_out, 
                y_true_col,
                y_pred_col,
                dfr_wp,
                dfr_model,
                dfr_project
            )

            return df_out, dfr_model, dfr_wp, dfr_project

        df_out, dfr_model, dfr_wp, dfr_project = run(
            X,
            y,
            codes,
            feature_selector_cls,
            model_cls,
            eval_metric_FS,
            HPs,
            df_out,
            dfr_model,
            dfr_wp,
            dfr_project,
            y_true_col,
            y_pred_col,
            wpts_filtered,
            progress_bar
        )

        return df0, df1, df2, df3, df4, df_out, dfr_model, dfr_wp, dfr_project
    
    def train_aip(self) -> None:
        return None 
    
    def forecast_aip(self) -> None:
        return None
