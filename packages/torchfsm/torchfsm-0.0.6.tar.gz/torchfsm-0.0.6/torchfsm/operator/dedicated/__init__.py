from ._navier_stokes import (VorticityConvection, 
                             NSPressureConvection,
                             Velocity2Pressure,
                             Vorticity2Pressure,
                             Vorticity2Velocity,
                             Leray)
from ._ks_convection import KSConvection
from ._gray_scott import (ChannelWisedDiffusion, GrayScottSource)