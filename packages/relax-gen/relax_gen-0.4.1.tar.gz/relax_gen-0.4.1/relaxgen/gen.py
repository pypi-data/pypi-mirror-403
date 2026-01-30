'''
Description:

En este archivo se econtraran diferentes modelos genéticos, de manera que se puedan utilizar en el proyecto
de manera sencilla y rápida.

Se agregarán más modelos conforme se vayan necesitando.
'''

# Import the algorithms to be used
from .algorithms.binary import alg_binary
from .algorithms.quantum import alg_quantum
from .algorithms.eda import alg_eda
from .algorithms.genetic_prog import alg_gp
from .algorithms.diff_evolution import alg_diff_evolution


class GEN():
    def __init__(self, funtion= None, population=None, num_genes = 8, num_cycles= 100, selection_percent = 0.5, 
                 crossing = 0.5, mutation_percent = 0.3, i_min = None, i_max = None, optimum = "max", 
                 num_qubits = 16, num_variables = 1, select_mode='ranking', datos=None, possibility_selection=0.5,
                 metric="mse", model="polynomial", max_depth=5, limits=None):
        self.funtion = funtion
        self.population = population
        self.num_genes = num_genes
        self.num_qubits = num_qubits
        self.num_cycles = num_cycles
        self.selection_percent = selection_percent
        self.crossing = crossing
        self.mutation_percent = mutation_percent
        self.i_min = i_min
        self.i_max = i_max
        self.optimum = optimum 
        self.num_variables = num_variables
        self.select_mode = select_mode
        self.datos = datos
        self.possibility_selection = possibility_selection
        self.metric = metric
        self.model = model
        self.max_depth = max_depth
        # Limits for DE algorithm
        self.limits = limits


    def binary(self): # Standard binary algorithm
        algorithm = alg_binary(
            self.funtion,
            self.population,
            self.num_genes,
            self.num_cycles,
            self.selection_percent,
            self.crossing,
            self.mutation_percent,
            self.i_min,
            self.i_max,
            self.optimum,
            self.select_mode,
            self.num_variables
        )
        return algorithm.optimize()

    def alg_quantum(self): # Quantum algorithm
        algorithm = alg_quantum(
            self.funtion,
            self.population,
            self.num_qubits,
            self.num_cycles,
            self.mutation_percent,
            self.i_min,
            self.i_max,
            self.optimum
        )
        return algorithm.optimize()
    

    def alg_eda(self): # EDA algorithm
        algorithm = alg_eda(
            self.datos,
            self.population,
            self.num_variables,
            self.num_cycles,
            self.i_min,
            self.i_max,
            self.possibility_selection,
            self.metric,
            self.model
        )

        return algorithm.optimize()

    def alg_gp(self): # Genetic programming algorithm
        algorithm = alg_gp(
            self.datos,
            self.population,
            self.num_cycles,
            self.max_depth
        )
        return algorithm.optimize()
    
    def alg_de(self): # Differential Evolution algorithm
        algorithm = alg_diff_evolution(
            function=self.funtion,
            population_size= self.population,
            num_variables=self.num_variables,
            mutation_factor=self.mutation_percent,
            crossover_rate=self.crossing,
            generations=self.num_cycles,
            limits=self.limits,
            optimum=self.optimum    
        )
        return algorithm.optimize()
