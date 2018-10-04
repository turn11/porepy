#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module contains superclass for mpfa and tpfa.
"""
import numpy as np
import scipy.sparse as sps

import porepy as pp


class FVElliptic(pp.numerics.mixed_dim.solver.Solver):
    """
    """

    def __init__(self, keyword):
        self.keyword = keyword

        # @ALL: We kee the physics keyword for now, or else we completely
        # break the parameter assignment workflow. The physics keyword will go
        # to be replaced by a more generalized approach, but one step at a time
        self.physics = keyword

    def key(self):
        return self.keyword + '_'


    def ndof(self, g):
        """
        Return the number of degrees of freedom associated to the method.
        In this case number of cells (pressure dof).

        Parameter
        ---------
        g: grid, or a subclass.

        Return
        ------
        dof: the number of degrees of freedom.

        """
        return g.num_cells


    def extract_pressure(self, g, solution_array, d):
        """ Extract the pressure part of a solution.

        The method is trivial for finite volume methods, with the pressure
        being the only primary variable.

        Parameters:
            g (grid): To which the solution array belongs.
            solution_array (np.array): Solution for this grid obtained from
                either a mono-dimensional or a mixed-dimensional problem.
            d (dictionary): Data dictionary associated with the grid. Not used,
                but included for consistency reasons.

        Returns:
            np.array (g.num_cells): Pressure solution vector. Will be identical
                to solution_array.

        """
        return solution_array


    def extract_flux(self, g, solution_array, d):
        """ Extract the flux related to a solution.

        The flux is computed from the discretization and the given pressure solution.

        @ALL: We should incrude the boundary condition as well?

        Parameters:
            g (grid): To which the solution array belongs.
            solution_array (np.array): Solution for this grid obtained from
                either a mono-dimensional or a mixed-dimensional problem. Will
                correspond to the pressure solution.
            d (dictionary): Data dictionary associated with the grid.

        Returns:
            np.array (g.num_faces): Flux vector.

        """
        flux_discretization = d[self.key() + 'flux']
        return flux_discretization * solution_array


    # ------------------------------------------------------------------------------#

    def assemble_matrix_rhs(self, g, data):
        return self.assemble_matrix(g, data), self.assemble_rhs(g, data)


    def assemble_matrix(self, g, data):
        """
        Return the matrix and right-hand side for a discretization of a second
        order elliptic equation using a FV method with a multi-point flux
        approximation.

        The name of data in the input dictionary (data) are:
        k : second_order_tensor
            Permeability defined cell-wise.
        bc : boundary conditions (optional)
        bc_val : dictionary (optional)
            Values of the boundary conditions. The dictionary has at most the
            following keys: 'dir' and 'neu', for Dirichlet and Neumann boundary
            conditions, respectively.

        Parameters
        ----------
        g : grid, or a subclass, with geometry fields computed.
        data: dictionary to store the data. For details on necessary keywords,
            see method discretize()

        Return
        ------
        matrix: sparse csr (g_num_cells, g_num_cells)
            Discretization matrix.

        """
        if not self.key() + 'flux' in data.keys():
            self.discretize(g, data)

        div = pp.fvutils.scalar_divergence(g)
        flux = data[self.key() + "flux"]
        M = div * flux

        return M

    # ------------------------------------------------------------------------------#

    def assemble_rhs(self, g, data):
        """
        Return the righ-hand side for a discretization of a second order elliptic
        equation using the MPFA method. See self.matrix_rhs for a detaild
        description.
        """
        if not self.key() + 'bound_flux' in data.keys():
            self.discretize(g, data)


        bound_flux = data[self.key() + "bound_flux"]

        param = data["param"]

        bc_val = param.get_bc_val(self)

        div = g.cell_faces.T

        return -div * bound_flux * bc_val

    def assemble_int_bound_flux(self, g, data, data_edge, grid_swap, cc, matrix, self_ind):

        div = g.cell_faces.T

        # Projection operators to grid
        mg = data_edge['mortar_grid']

        if grid_swap:
            proj = mg.slave_to_mortar_avg()
        else:
            proj = mg.master_to_mortar_avg()

        cc[self_ind, 2] += div * data[self.key() + 'bound_flux'] * proj.T

    def assemble_int_bound_source(self, g, data, data_edge, grid_swap, cc, matrix, self_ind):

        mg = data_edge['mortar_grid']

        if grid_swap:
            proj = mg.master_to_mortar_avg()
        else:
            proj = mg.slave_to_mortar_avg()

        cc[self_ind, 2] -= proj.T

    def assemble_int_bound_pressure_trace(self, g, data, data_edge, grid_swap, cc, matrix, self_ind):
        """ Assemble operators to represent the pressure trace.
        """
        mg = data_edge['mortar_grid']

        # TODO: this should become first or second or something
        if grid_swap:
            proj = mg.slave_to_mortar_avg()
        else:
            proj = mg.master_to_mortar_avg()

        bp = data[self.key() + 'bound_pressure_cell']
        cc[2, self_ind] += proj * bp
        cc[2, 2] += proj * data[self.key() + 'bound_pressure_face'] * proj.T


    def assemble_int_bound_pressure_cell(self, g, data, data_edge, grid_swap, cc, matrix, self_ind):
        mg = data_edge['mortar_grid']

        if grid_swap:
            proj = mg.master_to_mortar_avg()
        else:
            proj = mg.slave_to_mortar_avg()

        cc[2, self_ind] -= proj


    def enforce_neumann_int_bound(self, g_master, data_edge, matrix):
        """
        """
        # Operation is void for finite volume methods
        pass