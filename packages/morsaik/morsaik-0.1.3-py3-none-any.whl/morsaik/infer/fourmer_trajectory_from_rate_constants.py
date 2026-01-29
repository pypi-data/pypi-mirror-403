import jax.numpy as jnp
from warnings import warn
import timeit
from functools import partial

from ..obj.times_vector import TimesVector
from ..obj.motif_vector import (MotifVector,
                                _array_to_motif_vector_dct, _motif_vector_as_array)
from ..obj.motif_trajectory import MotifTrajectory
from ..obj.motif_production_vector import (MotifProductionVector,
                                           _motif_production_vector_as_array)
from ..obj.motif_breakage_vector import (MotifBreakageVector,
                                         _motif_breakage_vector_as_array)
from .fourmer_production_rates import _shape_fprc
from .fourmer_breakage_rates import _shape_brc

from scipy.integrate import solve_ivp
from jax.experimental.ode import odeint
from diffrax import diffeqsolve
import diffrax

import timeit

from .fourmer_production_rates import compute_total_extension_rates
from .fourmer_production_rates import _set_invalid_log_rates_to_logzero
from .fourmer_production_rates import _set_invalid_production_rates_to_zero
from .fourmer_breakage_rates import fourmer_breakage_rates
from .fourmer_mass_correction import mass_correction_rates

def fourmer_trajectory_from_rate_constants(
        motif_production_rate_constants : MotifProductionVector,
        motif_production_log_rate_constants : MotifProductionVector,
        breakage_rate_constants : MotifBreakageVector,
        initial_motif_concentrations_vector : MotifVector,
        times : TimesVector,
        complements : list,
        mass_correction_rate_constant : float = 0.,
        concentrations_are_logarithmized : bool = True,
        ode_integration_method : str = 'DOP853',
        execution_time_path : str = None,
        pseudo_count_concentration : float = 1.e-12,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None,
        first_step : float = None,
        ivp_atol : float = 1.e-6,
        ivp_rtol : float = 1.e-3,
    ) -> MotifTrajectory:
    """
    performs a fourmer reactor with the stated rate constants and initial
    conditions,
    i.e. integrates the motif ode with stated parameters.

    Parameters:
    -----------
    motif_production_rate_constants : MotifProductionVector,
    motif_production_log_rate_constants : MotifProductionVector,
    breakage_rate_constants : MotifBreakageVector,
    initial_motif_concentrations_vector : MotifVector,
    times : TimesVector,
    complements : list,
    mass_correction_rate_constant : float 
        Rate constant for compensation of numerical mass fluctuations,
        default 0.
    ode_integration_method : str
        default 'DOP853',
    execution_time_path : str
        if not None, the execution time of the ode integration is saved here
        default None,
    pseudo_count_concentration : float
        default 1.e-12,
    first_step : float
        default None
    ivp_atol : float
        atol for scipy.integrate.solve_ivp
        default 1.e-6
    ivp_rtol : float
        rtol for scipy.integrate.solve_ivp
        default 1.e-3

    Returns:
    --------
    motif_trajectory : MotifTrajectory
    """
    alphabet = initial_motif_concentrations_vector.alphabet
    motiflength = initial_motif_concentrations_vector.motiflength
    times_vector = times
    times = times.val
    if soft_reactant_threshold is None:
        soft_reactant_threshold = pseudo_count_concentration
    if motiflength!=4:
        raise ValueError("Motiflength ({}!=4) does not fit fourmer length.".format(motiflength))
    unit = initial_motif_concentrations_vector.unit
    if motiflength != 4:
        raise NotImplementedError("Motiflength needs to be four.")

    if breakage_rate_constants != 0.:
        breakage_rate_constants_array = _motif_breakage_vector_as_array(breakage_rate_constants)
    else:
        breakage_rate_constants_array = breakage_rate_constants
    #TODO assert breakage_rate_constants and motif_production_rate_constants
    # have fitting units with motif_trajectory

    initial_motif_concentrations_array = _motif_vector_as_array(initial_motif_concentrations_vector)
   
    motif_trajectory_field, times_array, execution_time = _integrate_motif_rate_equations(
        initial_motif_concentrations_array,
        number_of_letters = len(alphabet),
        motiflength=motiflength,
        complements=jnp.asarray(complements),
        concentrations_are_logarithmized = concentrations_are_logarithmized,
        fourmer_production_log_rate_constants = _motif_production_vector_as_array(motif_production_log_rate_constants),
        fourmer_production_rate_constants = _motif_production_vector_as_array(motif_production_rate_constants),
        breakage_rate_constants = breakage_rate_constants_array,
        mass_correction_rate_constant = mass_correction_rate_constant,
        t_eval = times,
        ode_integration_method = ode_integration_method,
        first_step = first_step,
        pseudo_count_concentration=pseudo_count_concentration,
        ivp_atol =ivp_atol,
        ivp_rtol = ivp_rtol,
        soft_reactant_threshold = soft_reactant_threshold,
        hard_reactant_threshold = hard_reactant_threshold
    )
    times_vector = TimesVector(times_array, times_vector.domain[0].units)
    motif_trajectory_array = motif_trajectory_field.reshape(times_array.shape+(len(alphabet)+1,)*motiflength)[:,:,1:]
    if execution_time_path is not None:
        with open(execution_time_path,'a') as f:
            f.write('\n'+str(execution_time))

    mv = MotifVector(motiflength, alphabet, unit)
    motif_vectors = [mv(_array_to_motif_vector_dct(motif_vector_array, motiflength, alphabet)) for motif_vector_array in motif_trajectory_array]
    return MotifTrajectory(motif_vectors, times_vector)

def _integrate_motif_rate_equations(
        initial_concentration_vector : jnp.ndarray,
        number_of_letters : int = 4,
        motiflength : int = 4,
        complements : list = jnp.array([1,0,3,2]),
        concentrations_are_logarithmized : bool = True,
        influx_rate_constants : jnp.ndarray = 0.,
        fourmer_production_log_rate_constants : jnp.ndarray = 0.,
        fourmer_production_rate_constants : jnp.ndarray = 1.,
        breakage_rate_constants : jnp.ndarray = 0.,
        mass_correction_rate_constant : float = 0.,
        t_eval : jnp.ndarray  = jnp.arange(0, 50000, 1),
        ode_integration_method : str = 'RK45',
        pseudo_count_concentration : float = 1.e-12,
        first_step = None,
        ivp_atol : float = 1.e-3,
        ivp_rtol : float = 1.e-6,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None
        ):
    """
    Parameters:
    -----------
    number_of_letters : int, optional
        number of letters
        default : 4
    motiflength : int, optional
        length of the tracked motifs
        default : 4
    complements : jnp.array, optional
        array of which letters are complementary to each other
        default : jnp.array([1,0,3,2])
    concentrations_are_logarithmized : boolean, optional (default True)
        specifies whether to use logconcentrations
    initial_concentration_vector : array
        array of initial concentrations of motifs
        default : None
    fourmer_production_log_rate_constants : array
        array of effective ligation rates
        default : None
    breakage_rate_constants : float or d-array,
        breakage_rate_constants, if float is given, all breakage_rate_constants
        are assumed to be the same.
        default: 0.
    ode_integration_method : string, optional
                    solve_ivp method
                    # explicit: # 'RK45' # 'RK23' # 'DOP853'
                    # implicit: # 'Radau' # 'BDF' # 'LSODA'
                    default : 'RK45'
    ivp_atol : float
        atol for scipy.integrate.solve_ivp
        default 1.e-6
    ivp_rtol : float
        rtol for scipy.integrate.solve_ivp
        default 1.e-3

    Return:
    -------
    x_0 : NIFTy field
        solution of the integrated ODE
    """
    if motiflength != 4: 
        raise NotImplementedError(f"{motiflength=}!=4")

    if soft_reactant_threshold is None:
        soft_reactant_threshold = pseudo_count_concentration
    motif_concentration_vector_shape = (number_of_letters+1,)*(motiflength)

    if initial_concentration_vector.size == number_of_letters*(number_of_letters+1)**(motiflength-1):
        n0 = jnp.zeros(motif_concentration_vector_shape)
        n0 = n0.at[:,1:].add(
                initial_concentration_vector.reshape((number_of_letters+1,number_of_letters)+(number_of_letters+1,)*(motiflength-2))
                )
    else:
        n0 = jnp.asarray(initial_concentration_vector).copy()

    fourmer_production_log_rate_constants = _shape_fprc(
            fourmer_production_log_rate_constants,
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            fprc_are_logarithmized = True
            )
    fourmer_production_rate_constants = _shape_fprc(
            fourmer_production_rate_constants,
            number_of_letters=number_of_letters,
            motiflength=motiflength,
            fprc_are_logarithmized = False
            )
    breakage_rate_constants = _shape_brc(
            breakage_rate_constants,
            number_of_letters=number_of_letters,
            motiflength=motiflength
            )

    if not concentrations_are_logarithmized:
        warn(f"motif rate equation only implemented for log concentrations to ensure positivity, will transform them to log concentrations with pseudo_count {pseudo_count_concentration} for the sake of the ode integration.")
        n0 = n0.at[n0<pseudo_count_concentration].set(pseudo_count_concentration)
        n0 = jnp.log(n0)
    n0 = n0.flatten()
    t0, t1, t_eval = _shape_t_eval(t_eval)
    rate_equations, args = _build_rate_equations(
            soft_reactant_threshold = soft_reactant_threshold,
            hard_reactant_threshold = hard_reactant_threshold,
            influx_rate_constants = influx_rate_constants,
            fourmer_production_log_rate_constants = fourmer_production_log_rate_constants,
            fourmer_production_rate_constants = fourmer_production_rate_constants,
            breakage_rate_constants = breakage_rate_constants,
            complements = complements,
            motiflength = motiflength,
            mass_correction_rate_constant = mass_correction_rate_constant,
            initial_log_concentration_array = n0.reshape(motif_concentration_vector_shape)
            )
    print(f"{args.keys() = }")
    timing_dct = {"execution_time" : None}
    timing_dct["execution_time"] = - timeit.default_timer()
    if ode_integration_method in ['RK45','RK23','DOP853','Radau','LSODA','BDF',]:
        # integrate ode
        r = solve_ivp(
                rate_equations,
                [t0,t1],
                n0,
                t_eval = t_eval,
                args = (args,),
                method = ode_integration_method,
                first_step=first_step,
                atol=ivp_atol,
                rtol=ivp_rtol,
                dense_output=True,
                )
        if not r.success:
            print(f"solve_ivp unsuccesful (probably uncomplete solution)")
            print(f"got the following message: {r.message}")
        motif_concentration_trajectory = jnp.asarray(r.y)
        times_array = jnp.asarray(r.t)
    elif ode_integration_method == 'Dopri':
        sol = odeint(
                rate_equations, #func
                n0, #y0
                t_eval, #t
                (args,), #args
                rtol=ivp_rtol,
                atol=ivp_atol,
                )
        times_array = jnp.asarray(t_eval)
        motif_concentration_trajectory = jnp.asarray(sol)
    else:
        rate_equations = diffrax.ODETerm(rate_equations)
        # Dopri5, Dopri8
        solver = diffrax.Dopri5()
        dt0 = None
        stepsize_controller = diffrax.PIDController(rtol=ivp_rtol,atol=ivp_atol)
        save_at = diffrax.SaveAt(ts=t_eval)
        r = diffeqsolve(
                rate_equations,
                solver,
                t0=t0,
                t1=t1,
                dt0=dt0,
                y0=n0,
                args = args,
                saveat = save_at,
                stepsize_controller=stepsize_controller
                )
        times_array = jnp.asarray(r.ts)
        motif_concentration_trajectory = jnp.asarray(r.ys)
    timing_dct["execution_time"] += timeit.default_timer()
    if not concentrations_are_logarithmized:
        motif_concentration_trajectory = jnp.exp(motif_concentration_trajectory)
    return jnp.asarray(motif_concentration_trajectory).T, jnp.asarray(times_array), timing_dct

def _shape_t_eval(t_eval):
    if len(t_eval)==1:
        t0=0
        t1=t_eval
        t_eval = None
    else:
        t0 = t_eval[0]
        t1 = t_eval[-1]
    return t0, t1, t_eval

def _build_rate_equations(
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None,
        **kwargs,
        ):
    """
        influx_rate_constants : jnp.ndarray = 0.,
        breakage_rate_constants : jnp.ndarray,
        fourmer_production_log_rate_constants : jnp.ndarray = 0.,
        fourmer_production_rate_constants : jnp.ndarray = 0.,
        complements : list = jnp.array([1,0,3,2]),
        motiflength : int = 4,
    """
    print(f"{kwargs.keys() = }")
    kwargs.setdefault('influx_rate_constants', 0.)
    kwargs.setdefault('fourmer_production_log_rate_constants', 0.)
    kwargs.setdefault(' fourmer_production_rate_constants',  0.)
    kwargs.setdefault('breakage_rate_constants',0.)
    kwargs.setdefault('complements', jnp.array([1,0,3,2]))
    kwargs.setdefault('motiflength', 4)
    kwargs.setdefault('mass_correction_rate_constant', 0.)
    print(f"{kwargs.keys() = }")
    if kwargs['mass_correction_rate_constant'] != 0.:
        if 'initial_log_concentration_array' not in kwargs.keys():
            raise TypeError("For mass_correction_rate_constant != 0, initial_log_concentration_array needs to be specified")
    rate_equations = _fourmer_rate_equations(kwargs,
                                             soft_reactant_threshold = soft_reactant_threshold,
                                             hard_reactant_threshold = hard_reactant_threshold)
    return rate_equations, kwargs

def _fourmer_production_equations(
        t, y, arg1,
        soft_reactant_threshold : float = 0.,
        hard_reactant_threshold : float = None
        ):
    """
    arg1 = ([influx_rate_constants,
             (fourmer_production_log_rate_constants,fourmer_production_rate_constants),
             complements,
             motiflength],)

    """
    leerc = arg1['fourmer_production_log_rate_constants']
    eerc=arg1['fourmer_production_rate_constants']
    complements = arg1['complements']
    motiflength = arg1['motiflength']
    if eerc.shape[0] == eerc.shape[1]:
        eerc = eerc[:,1:,1:,:,:,1:,1:,:]
    if leerc.shape[0] == leerc.shape[1]:
        leerc = leerc[:,1:,1:,:,:,1:,1:,:]
    return jnp.asarray(compute_total_extension_rates(
        jnp.asarray(y.reshape((len(complements)+1,)*motiflength)),
        log_rate_constants = leerc,
        rate_constants = eerc,
        motiflength = 4,
        number_of_letters = eerc.shape[1],
        soft_reactant_threshold = soft_reactant_threshold,
        hard_reactant_threshold = hard_reactant_threshold
        )).reshape(-1)

def _fourmer_influx_equations(t, y, arg):
    return arg['influx_rate_constants'].reshape(-1)*jnp.exp(-y).reshape(-1)

def _fourmer_breakage_equations(
        t, y, arg2,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None
        ):
    """
    arg2 : dict
        specify 'breakage_rate_constants', 'complements', 'motiflength'
    soft_reactant_threshold : float
        minimal concentration of a reactant to contribute fully to a reaction,
        for smaller concentrations the reaction rates get damped or clipped
        default : 0., i.e. clipping deactivated
    hard_reactant_threshold : float
       concentration of a reactant at which all its reactions are set to zero.
       Between 'soft_reactant_threshold' and 'hard_reactant_threshold' the reaction rates smoothly
       transition between fully contribution of the reactant and clipping
       via a cos-funtion.
       Default : None, setting hard_reactant_threshold to soft_reactant_threshold/2
    """
    if not isinstance(arg2,dict):
        raise TypeError("arg2 supposed to be dictionary")
    arg2.setdefault('breakage_rate_constants',0.)
    arg2.setdefault('complements', jnp.array([1,0,3,2]))
    arg2.setdefault('motiflength', 4)
    breakage_rate_constants = arg2['breakage_rate_constants']
    complements = arg2['complements']
    motiflength = arg2['motiflength']

    breakage_logc_diff = fourmer_breakage_rates(
            y.reshape((complements.size+1,)*motiflength),
            effective_breakage_rate_constants = breakage_rate_constants,
            soft_reactant_threshold = soft_reactant_threshold,
            hard_reactant_threshold = hard_reactant_threshold
            )
    return breakage_logc_diff.reshape(-1)

def _fourmer_mass_correction_rates(t,y, arg3):
    initial_log_concentration_array = arg3['initial_log_concentration_array']
    mass_correction_rate_constant = arg3['mass_correction_rate_constant']
    complements = arg3['complements']
    motiflength = arg3['motiflength']
    return mass_correction_rates(
            initial_log_concentration_array,
            y.reshape((complements.size+1,)*motiflength),
            weight = mass_correction_rate_constant).reshape(-1)

def _fourmer_rate_equations(
        kwargs,
        soft_reactant_threshold : float = None,
        hard_reactant_threshold : float = None
        ):
    """
    returns a function: the rate equation with arguments
    t, y, args : dict; 
    args = [influx_rate_constants,
             fourmer_production_log_rate_constants,
             fourmer_production_rate_constants,
             breakage_rate_constants,
             complements,
             motiflength,
             mass_correction_rate_constant,
             initial_log_concentration_array
             ],
    """
    exclude_influx =  jnp.all(jnp.asarray(kwargs['influx_rate_constants']) == 0.)
    include_influx = 1-exclude_influx
    if exclude_influx:
        print("Influx rate constants equal 0, thus, influx turned off.")
    exclude_breakage = jnp.all(kwargs['breakage_rate_constants'] == 0.)
    include_breakage = 1-exclude_breakage
    if exclude_breakage:
        print("Breakage rate constant equals 0, thus, breakage turned off.")
    exclude_extension = jnp.all(kwargs['fourmer_production_rate_constants']==0.)
    include_extension = 1-exclude_extension
    if exclude_extension:
        print("Extension rate constants equal 0, thus, fourmer extension turned off.")
    exclude_mass_correction = bool(kwargs['mass_correction_rate_constant']==0.)
    include_mass_correction = 1-exclude_mass_correction
    if exclude_mass_correction:
        print("Mass correction rate constant equals 0, thus, mass correction turned off.")
    def fre(t,y,args):
        freturn = jnp.zeros(y.shape)
        if include_influx:
            freturn = freturn + _fourmer_influx_equations(t, y, args)
        if include_breakage:
            freturn = freturn + _fourmer_breakage_equations(t, y, args,
                                                            soft_reactant_threshold=soft_reactant_threshold,
                                                            hard_reactant_threshold=hard_reactant_threshold)
        if include_extension:
            freturn = freturn + _fourmer_production_equations(t, y, args,
                                                              soft_reactant_threshold=soft_reactant_threshold,
                                                              hard_reactant_threshold=hard_reactant_threshold)
        if include_mass_correction:
            freturn = freturn + _fourmer_mass_correction_rates(t, y, args)
        return freturn
    return fre
