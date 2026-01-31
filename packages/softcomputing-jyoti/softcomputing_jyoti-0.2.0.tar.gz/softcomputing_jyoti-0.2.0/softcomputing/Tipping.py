import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

quality = ctrl.Antecedent(np.arange(0, 11, 1), 'quality')
service = ctrl.Antecedent(np.arange(0, 11, 1), 'service')
tip = ctrl.Consequent(np.arange(0, 26, 1), 'tip')

quality['poor'] = fuzz.trimf'triangualr memnership function'(quality.universe, [0, 0, 5])
quality['good'] = fuzz.trimf(quality.universe, [5, 10, 10])

service['poor'] = fuzz.trimf(service.universe, [0, 0, 5])
service['good'] = fuzz.trimf(service.universe, [5, 10, 10])

tip['low'] = fuzz.trimf(tip.universe, [0, 0, 10])
tip['high'] = fuzz.trimf(tip.universe, [10, 25, 25])

rule1 = ctrl.Rule(quality['poor'] | service['poor'], tip['low'])
rule2 = ctrl.Rule(quality['good'] & service['good'], tip['high'])

tipping_system = ctrl.ControlSystem([rule1, rule2])
tipping = ctrl.ControlSystemSimulation(tipping_system)

tipping.input['quality'] = 6
tipping.input['service'] = 8

tipping.compute()

print("Recommended Tip:", tipping.output['tip'])
