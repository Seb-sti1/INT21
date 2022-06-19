# Simple script that simulates a bot moving inside an Arena, following a series of commands
# by Alberto Tonda, 2018 <alberto.tonda@gmail.com>

import sys
import inspyred
import random
import math
import numpy as np
from shapely.geometry import Polygon, LineString, Point

random_number_generator = random.Random()
random_number_generator.seed(42)  # seeding the generators with a fixed value ensures that you will always obtain the same sequence of numbers at every run


def moveRobot(robotX, robotY, robotDegrees, distance):
    robotX += distance * math.cos(robotDegrees * math.pi / 180)
    robotY += distance * math.sin(robotDegrees * math.pi / 180)
    return [robotX, robotY]


def rotateRobot(robotX, robotY, robotDegrees, angle):
    return robotDegrees + angle


def applicateCommands(robotX, robotY, robotDegrees, listOfCommands):
    number_of_commands = len(listOfCommands) // 2
    line_points = [(robotX, robotY)]

    for i in range(number_of_commands):
        robotDegrees = rotateRobot(robotX, robotY, robotDegrees, listOfCommands[2 * i])
        [robotX, robotY] = moveRobot(robotX, robotY, robotDegrees, listOfCommands[2 * i + 1])
        line_points.append((robotX, robotY))

    return robotX, robotY, robotDegrees, line_points


'''This function accepts in input a list of strings, and tries to parse them to update the position of a robot. Then 
returns distance from objective. '''


def fitnessRobot(listOfCommands, visualize=True):
    # the Arena is a 100 x 100 pixel space
    arenaLength = 100
    arenaWidth = 100

    # let's also put a couple of walls in the arena; walls are described by a set of 4 (x,y) corners (bottom-left, top-left, top-right, bottom-right)
    walls = []

    wall1 = dict()
    wall1["x"] = 30
    wall1["y"] = 0
    wall1["width"] = 10
    wall1["height"] = 80

    wall2 = dict()
    wall2["x"] = 70
    wall2["y"] = 20
    wall2["width"] = 10
    wall2["height"] = 80

    walls.append(wall1)
    walls.append(wall2)

    labyrinthe_wall1 = Polygon([(wall1["x"], wall1["y"]), (wall1["x"] + wall1["width"], wall1["y"]),
                                (wall1["x"] + wall1["width"], wall1["y"] + wall1["height"]),
                                (wall1["x"], wall1["y"] + wall1["height"])])
    labyrinthe_wall2 = Polygon([(wall2["x"], wall2["y"]), (wall2["x"] + wall2["width"], wall2["y"]),
                                (wall2["x"] + wall2["width"], wall2["y"] + wall2["height"]),
                                (wall2["x"], wall2["y"] + wall2["height"])])

    labyrinthe_arena = LineString([(0, 0), (0, arenaLength), (arenaWidth, arenaLength), (arenaWidth, 0), (0, 0)])

    # initial position and orientation of the robot
    startX = robotX = 10
    startY = robotY = 10
    startDegrees = robotDegrees = 90  # 90°

    # position of the objective
    objectiveX = 90
    objectiveY = 90

    # this is a list of points that the robot will visit; used later to visualize its path

    # move robot, check that the robot stays inside the arena and stop movement if a wall is hit
    robotX, robotY, robotDegrees, positions = applicateCommands(robotX, robotY, robotDegrees, listOfCommands)

    distanceFromObjective = math.sqrt((robotX - objectiveX) ** 2 + (robotY - objectiveY) ** 2)

    #add a huge malus if the robot leaves the arena
    if len(positions) > 1:
        line = LineString(positions)
        intersectionArenaMalus = 1000
        if line.intersects(labyrinthe_arena) : distanceFromObjective += intersectionArenaMalus
    
    # nb of walls between objective and final position of the robot
    MalusFromHorizon = 300
    WallsBeforeEnd = 0
    
    distanceLine = LineString([positions[-1],(objectiveX,objectiveY)])
    if distanceLine.intersects(labyrinthe_wall1) :
        WallsBeforeEnd += MalusFromHorizon
    if distanceLine.intersects(labyrinthe_wall2) : 
        WallsBeforeEnd += MalusFromHorizon

    # calcule the length of the path
    LengthPath = 0
    
    # for each time the robot goes through a wall, a malus is added
    malusGain = 100
    closeToWallMalus = 0 # init malus to 0

    for k in range(len(positions)-1): # add malus everytime the path encounters a wall
        currentLine = LineString([(positions[k]), (positions[k+1])])
        LengthPath += currentLine.length
        if currentLine.intersects(labyrinthe_wall1) : closeToWallMalus += malusGain
        if currentLine.intersects(labyrinthe_wall2) : closeToWallMalus += malusGain

    fitness = distanceFromObjective + closeToWallMalus + WallsBeforeEnd 

    # this is optional, argument "visualize" has to be explicitly set to "True" when function is called
    if visualize:

        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        figure = plt.figure()
        ax = figure.add_subplot(111)

        # plot initial position and objective
        ax.plot(startX, startY, 'r^', label="Initial position of the robot")
        ax.plot(objectiveX, objectiveY, 'gx', label="Position of the objective")

        # plot the walls
        for wall in walls:
            ax.add_patch(patches.Rectangle((wall["x"], wall["y"]), wall["width"], wall["height"]))

        # plot a series of lines describing the movement of the robot in the arena
        for i in range(1, len(positions)):
            ax.plot([positions[i - 1][0], positions[i][0]], [positions[i - 1][1], positions[i][1]], 'r-') #,label="Robot path")

        ax.set_title("Movements of the robot inside the arena")
        ax.legend(loc='best')
        plt.ioff()
        plt.show()

    return fitness


def evaluate(candidates, args):
    scores = []

    for candidate in candidates:
        scores.append(fitnessRobot(candidate, False))

    return scores


# this function generates initial random commands for the robot; it needs a random number generator (called "random") and a dictionary or arguments in input,
# to be used by the EvolutionaryComputation object; returns one (randomly generated) candidate individual
def generator_commands(random, args):
    minimum_angle = args["minimum_angle"]  # also, the minimum value of each dimension will be specified later in "args"
    maximum_angle = args["maximum_angle"]  # same goes for the maximum value

    minimum_distance = args[
        "minimum_distance"]  # also, the minimum value of each dimension will be specified later in "args"
    maximum_distance = args["maximum_distance"]  # same goes for the maximum value

    max_individual_length = args["max_individual_length"]
    min_individual_length = args["min_individual_length"]

    # the individual will be a series of "number_of_dimensions" random values, generated between "minimum" and "maximum"
    # the individual will be a series of commands (move and rotate)

    individual_length = random_number_generator.randint(min_individual_length, max_individual_length) // 2 * 2
    individual = np.zeros(individual_length)

    for i in range(0, individual_length // 2):
        individual[2 * i] = random_number_generator.uniform(minimum_angle, maximum_angle)
        individual[2 * i + 1] = random_number_generator.uniform(minimum_distance, maximum_distance)

    return individual


################# MAIN
def main():
    # instantiate the evolutionary algorithm object
    evolutionary_algorithm = inspyred.ec.EvolutionaryComputation(random_number_generator)
    # and now, we specify every part of the evolutionary algorithm
    evolutionary_algorithm.selector = inspyred.ec.selectors.tournament_selection  # by default, tournament selection has tau=2 (two individuals), but it can be modified (see below)
    evolutionary_algorithm.variator = [inspyred.ec.variators.uniform_crossover,
                                       inspyred.ec.variators.gaussian_mutation]  # the genetic operators are put in a list, and executed one after the other
    evolutionary_algorithm.replacer = inspyred.ec.replacers.plus_replacement  # "plus" -> "mu+lambda"
    evolutionary_algorithm.terminator = inspyred.ec.terminators.evaluation_termination  # the algorithm terminates when a given number of evaluations (see below) is reached

    # evolutionary_algorithm.observer = inspyred.ec.observers.best_observer # prints best individual to screen
    # evolutionary_algorithm.observer = inspyred.ec.observers.stats_observer # print out population statistics
    evolutionary_algorithm.observer = inspyred.ec.observers.plot_observer  # plots evolution
    final_population = evolutionary_algorithm.evolve(
        generator=generator_commands,  # of course, we need to specify the evaluator
        evaluator=evaluate,  # and the corresponding evaluator
        pop_size=300,  # size of the population
        num_selected=2000,  # size of the offspring (children individuals)
        maximize=False,  # this is a minimization problem, but inspyred can also manage maximization problem
        max_evaluations=200000,  # maximum number of evaluations before stopping, used by the terminator
        tournament_size=2,
        # size of the tournament selection; we need to specify it only if we need it different from 2
        crossover_rate=0.7,  # probability of applying crossover
        mutation_rate=0.3,  # probability of applying mutation

        # all arguments specified below, THAT ARE NOT part of the "evolve" method, will be automatically placed in "args"
        min_individual_length=30,
        max_individual_length=100,  # number of dimensions of the problem, used by "generator_weierstrass"
        minimum_angle=-90,  # minimum angle for generator_commands
        maximum_angle=90,  # maximum angle
        minimum_distance=0,  # minimum distance for generator_commands
        maximum_distance=30,  # maximum distance
    )

    # after the evolution is over, the resulting population is stored in "final_population"; the best individual is on the top
    best_individual = final_population[0]
    print("The best individual has fitness %.2f" % best_individual.fitness)

    fitnessRobot(best_individual.candidate, visualize=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())