import numpy as np
import scipy.sparse as sps

from core.solver.solver import *

class Mass(Solver):

#------------------------------------------------------------------------------#

    def ndof(self, g):
        """
        Return the number of degrees of freedom associated to the method.
        In this case number of cells.

        Parameter
        ---------
        g: grid, or a subclass.

        Return
        ------
        dof: the number of degrees of freedom.

        """
        return g.num_cells

#------------------------------------------------------------------------------#

    def matrix_rhs(self, g, data):
        """
        Return the matrix and righ-hand side (null) for a discretization of a
        L2-mass bilinear form with constant test and trial functions.

        The name of data in the input dictionary (data) are:
        phi: array (self.g.num_cells)
            Scalar values which represent the porosity.
            If not given assumed unitary.
        deltaT: Time step for a possible temporal discretization scheme.
            If not given assumed unitary.

        Parameters
        ----------
        g : grid, or a subclass, with geometry fields computed.
        data: dictionary to store the data.

        Return
        ------
        matrix: sparse dia (g.num_cells, g_num_cells)
            Mass matrix obtained from the discretization.
        rhs: array (g_num_cells)
            Null right-hand side.

        Examples
        --------
        data = {'deltaT': 1e-2, 'phi': 0.3*np.ones(g.num_cells)}
        M, _ = mass.Mass().matrix_rhs(g, data)
        invM = mass.Mass().inv(M)

        """
        ndof = self.ndof(g)
        coeff = g.cell_volumes * data.get('phi', np.ones(ndof)) / \
                data.get('deltaT', np.ones(ndof))

        return sps.dia_matrix((coeff, 0), shape=(ndof, ndof)), np.zeros(ndof)

#------------------------------------------------------------------------------#

    def inv(self, matrix):
        """
        Return the inverse of the matrix for this method.

        Parameters
        ----------
        g : grid, or a subclass, with geometry fields computed.

        Return
        ------
        matrix: sparse dia (g.num_cells, g_num_cells)
            Inverse of the mass matrix obtained from the discretization.

        """
        return sps.dia_matrix((1./matrix.diagonal(), 0), shape=matrix.shape)

#------------------------------------------------------------------------------#
