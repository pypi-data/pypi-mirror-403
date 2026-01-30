from .gen import GEN
from .algorithms.binary import alg_binary
from .algorithms.quantum import alg_quantum
from .algorithms.eda import alg_eda
from .algorithms.genetic_prog import alg_gp
from .algorithms.diff_evolution import alg_diff_evolution

class RelaxGEN(GEN):
    def __init__(self, funtion=None, population=None, **kwargs):
        super().__init__(funtion, population, **kwargs)
        self.num_genes = kwargs.get("num_genes")  
        self.num_cycles = kwargs.get("num_cycles") 
        self.selection_percent = kwargs.get("selection_percent") 
        self.crossing = kwargs.get("crossing") 
        self.mutation_percent = kwargs.get("mutation_percent") 
        self.i_min = kwargs.get("i_min")
        self.i_max = kwargs.get("i_max")
        self.optimum = kwargs.get("optimum")
        self.num_qubits = kwargs.get("num_qubits")
        self.select_mode = kwargs.get("select_mode")
        self.num_variables = kwargs.get("num_variables")
        self.data = kwargs.get("data")
        self.possibility_selection = kwargs.get("possibility_selection")
        self.metric = kwargs.get("metric")
        self.model = kwargs.get("model")
        self.max_depth = kwargs.get("max_depth")
        self.limits = kwargs.get("limits")


    
    def binary(self):
        algorithm = alg_binary(
            funtion=self.funtion,
            population=self.population,
            cant_genes=self.num_genes,
            cant_ciclos=self.num_cycles,
            selection_percent=self.selection_percent,
            crossing=self.crossing,
            mutation_percent=self.mutation_percent,
            i_min=self.i_min,
            i_max=self.i_max,
            optimum=self.optimum,
            num_variables=self.num_variables,
            select_mode=self.select_mode
        )
        return algorithm.optimize()

    def alg_quantum(self):
        algorithm = alg_quantum(
            funtion=self.funtion,
            population=self.population,
            num_qubits=self.num_qubits,
            cant_ciclos=self.num_cycles,
            mutation_percent=self.mutation_percent,
            i_min=self.i_min,
            i_max=self.i_max,
            optimum=self.optimum
        )
        return algorithm.optimize()
    
    def alg_eda(self):
        algorithm = alg_eda(
            datos = self.data,
            population=self.population,
            num_variables=self.num_variables,
            num_ciclos=self.num_cycles,
            i_min=self.i_min,
            i_max=self.i_max,
            possibility_selection=self.possibility_selection,
            metric=self.metric,
            model=self.model
        )
        return algorithm.optimize()
    
    def alg_gp(self): # Genetic programming algorithm
        algorithm = alg_gp(
            data = self.data,
            population = self.population,
            num_cycles = self.num_cycles,
            max_depth = self.max_depth
        )
        return algorithm.optimize()
    

    def alg_de(self): # Differential Evolution algorithm
        algorithm = alg_diff_evolution(
            function=self.funtion,
            population_size=self.population,
            num_variables=self.num_variables,
            mutation_factor=self.mutation_percent,
            crossover_rate=self.crossing,
            generations=self.num_cycles,
            limits=self.limits,
            optimum=self.optimum    
        )
        return algorithm.optimize()