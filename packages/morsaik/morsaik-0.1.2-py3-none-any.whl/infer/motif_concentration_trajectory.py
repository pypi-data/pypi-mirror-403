from ..obj.motif_trajectory import MotifTrajectory
from ..obj.motif_trajectory import _motif_trajectory_as_array
from ..obj.motif_trajectory import _array_to_motif_trajectory
from ..obj.units import make_unit, Unit

def motif_concentration_trajectory_from_motif_number_trajectory(
        motif_number_trajectory : MotifTrajectory,
        c_ref : float,
        unit : Unit = make_unit('mol')/make_unit('L')
        ) -> MotifTrajectory:
    single_particle_concentration = c_ref/motif_number_trajectory.motifs['length1strand'].val[0][0]

    motif_number_trajectory_array, _ = _motif_trajectory_as_array(
            motif_number_trajectory
            )
    motif_concentration_trajectory_array = single_particle_concentration*motif_number_trajectory_array
    return _array_to_motif_trajectory(
            motif_concentration_trajectory_array,
            motif_number_trajectory.times,
            motiflength  = motif_number_trajectory.motiflength,
            alphabet = motif_number_trajectory.alphabet,
            unit = unit
            )
