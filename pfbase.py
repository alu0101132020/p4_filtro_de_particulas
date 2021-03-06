#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Rob�tica Computacional -
# Grado en Ingenier�a Inform�tica (Cuarto)
# Pr�ctica: Filtros de particulas.

from math import *
from robot import *
import random
import numpy as np
import matplotlib.pyplot as plt
import sys
import select
from datetime import datetime
# ******************************************************************************
# Declaraci�n de funciones

def distancia(a,b):
  # Distancia entre dos puntos (admite poses)
  return np.linalg.norm(np.subtract(a[:2],b[:2]))

def angulo_rel(pose,p):
  # Diferencia angular entre una pose y un punto objetivo 'p'
  w = atan2(p[1]-pose[1],p[0]-pose[0])-pose[2]
  while w >  pi: w -= 2*pi
  while w < -pi: w += 2*pi
  return w

def pinta(secuencia,args):
  # Dibujar una secuencia de puntos
  t = np.array(secuencia).T.tolist()
  plt.plot(t[0],t[1],args)

def mostrar(objetivos,trayectoria,trayectreal,filtro):
  # Mostrar mapa y trayectoria
  plt.ion() # modo interactivo
  plt.clf()
  plt.axis('equal')
  # Fijar los bordes del gr�fico
  objT   = np.array(objetivos).T.tolist()
  bordes = [min(objT[0]),max(objT[0]),min(objT[1]),max(objT[1])]
  centro = [(bordes[0]+bordes[1])/2.,(bordes[2]+bordes[3])/2.]
  radio  = max(bordes[1]-bordes[0],bordes[3]-bordes[2])
  plt.xlim(centro[0]-radio,centro[0]+radio)
  plt.ylim(centro[1]-radio,centro[1]+radio)
  # Representar mapa
  for p in filtro:
    dx = cos(p.orientation)*.05
    dy = sin(p.orientation)*.05
    plt.arrow(p.x,p.y,dx,dy,head_width=.05,head_length=.05,color='k')
  pinta(trayectoria,'--g')
  pinta(trayectreal,'-r')
  pinta(objetivos,'-.ob')
  p = hipotesis(filtro)
  dx = cos(p[2])*.05
  dy = sin(p[2])*.05
  plt.arrow(p[0],p[1],dx,dy,head_width=.075,head_length=.075,color='m')
  # Mostrar y comprobar pulsaciones de teclado:
  plt.draw()
#  if sys.stdin in select.select([sys.stdin],[],[],.01)[0]:
#    line = sys.stdin.readline()
  raw_input()

def genera_filtro(num_particulas, balizas, real, centro=[2,2], radio=2):
  # Creamos el array de robots
  robots = []
  for i in range(num_particulas):
    # Generamos para cada partícula un valor aleatorio entre el círculo inicial
    # y un radio. Para la orientación del robot también generamos un valor aleatorio
    x_random_value = random.random()
    if (x_random_value > 0.5):
      x_random = centro[0] + random.random() * radio
    else:
      x_random = centro[0] - random.random() * radio
    y_random_value = random.random()
    if (y_random_value > 0.5):
      y_random = centro[1] + random.random() * radio
    else:
      y_random = centro[1] - random.random() * radio

    orientation_random = random.random() * 2 * pi
    # Creamos el robot y calculamos su peso asociado.
    new_robot = robot()
    new_robot.set(x_random, y_random, orientation_random)
    new_robot.set_noise(.01,.01,.01)
    new_robot.measurement_prob(real.sense(balizas), balizas)
    # Añadimos el robot al conjunto.
    robots.append(new_robot)
  return robots



def dispersion(filtro):
  # Dispersion espacial del filtro de particulas
  # Dispersion espacial del filtro de particulas
  max_x = -inf
  max_y = -inf
  min_x = inf
  min_y = inf

  for robot in filtro:
    pos = robot.pose()
    if(pos[0] > max_x):
      max_x = pos[0]
    if(pos[0] < min_x):
      min_x = pos[0]
    if(pos[0] > max_y):
      max_y = pos[1]
    if(pos[0] < min_y):
      min_y = pos[1]

    return [max_x, min_x, max_y, min_y]

def peso_medio(filtro):
  # Peso medio normalizado del filtro de particulas
  suma = 0
  for robot in filtro:
    suma += robot.weight
  return suma / len(filtro)

# ******************************************************************************

random.seed(0)

# Definici�n del robot:
P_INICIAL = [-1,-1,0.] # Pose inicial (posici�n y orientacion)
V_LINEAL  = .7         # Velocidad lineal    (m/s)
V_ANGULAR = 140.       # Velocidad angular   (�/s)
FPS       = 10.        # Resoluci�n temporal (fps)
HOLONOMICO = 0         # Robot holon�mico
GIROPARADO = 0         # Si tiene que tener vel. lineal 0 para girar
LONGITUD   = .1        # Longitud del robot

N_PARTIC  = 200         # Tama�o del filtro de part�culas
N_INICIAL = 1000       # Tama�o inicial del filtro

# Definici�n de trayectorias:
trayectorias = [
    [[0,2],[4,2]],
    [[2,4],[4,0],[0,0]],
    [[2,4],[2,0],[0,2],[4,2]],
    [[2+2*sin(.4*pi*i),2+2*cos(.4*pi*i)] for i in range(5)],
    [[2+2*sin(.8*pi*i),2+2*cos(.8*pi*i)] for i in range(5)],
    [[2+2*sin(1.2*pi*i),2+2*cos(1.2*pi*i)] for i in range(5)],
    [[2*(i+1),4*(1+cos(pi*i))] for i in range(6)],
    [[2+.2*(22-i)*sin(.1*pi*i),2+.2*(22-i)*cos(.1*pi*i)] for i in range(20)],
    [[2+(22-i)/5*sin(.1*pi*i),2+(22-i)/5*cos(.1*pi*i)] for i in range(20)]
    ]

# Definici�n de los puntos objetivo:
if len(sys.argv)<2 or int(sys.argv[1])<0 or int(sys.argv[1])>=len(trayectorias):
  sys.exit(sys.argv[0]+" <�ndice entre 0 y "+str(len(trayectorias)-1)+">")
objetivos = trayectorias[int(sys.argv[1])]

# Definici�n de constantes:
EPSILON = .1                # Umbral de distancia
V = V_LINEAL/FPS            # Metros por fotograma
W = V_ANGULAR*pi/(180*FPS)  # Radianes por fotograma

real = robot()
real.set_noise(.01,.01,.01) # Ruido lineal / radial / de sensado
real.set(*P_INICIAL)

#inicializaci�n del filtro de part�culas y de la trayectoria
initial_pos = [P_INICIAL[0], P_INICIAL[1]]
pf = genera_filtro(N_INICIAL, objetivos, real, initial_pos, 0.5)

trayectreal = [real.pose()]
trayectoria = [hipotesis(pf)]

tiempo  = 0.
espacio = 0.
for punto in objetivos:
  while distancia(trayectoria[-1],punto) > EPSILON and len(trayectoria) <= 1000:
    # Escogemos el mejor robot del filtro
    pose = hipotesis(pf)
    # Movemos todos los robots en base al mejor robot.
    w = angulo_rel(pose,punto)
    if w > W:  w =  W
    if w < -W: w = -W
    v = distancia(pose,punto)
    if (v > V): v = V
    if (v < 0): v = 0
    if HOLONOMICO:
      if GIROPARADO and abs(w) > .01:v = 0
      real.move(w,v) 
      for i in range(len(pf)):
        pf[i].move(w, v)
    else:
      real.move_triciclo(w,v,LONGITUD)
      for i in range(len(pf)):
        pf[i].move_triciclo(w, v, LONGITUD)
    # Añadimos a la trayectoria la mejor calculada y la real.
    trayectoria.append(hipotesis(pf))
    trayectreal.append(real.pose())
    mostrar(objetivos,trayectoria,trayectreal, pf)
    # remuestreo
    pf = resample(pf, N_PARTIC)
      #recalculamos el peso de cada robot (la función los pone a 1)
    for particle in pf:
      particle.measurement_prob(real.sense(objetivos), objetivos)
    
    espacio += v
    tiempo  += 1

if len(trayectoria) > 1000:
  print "<< ! >> Puede que no se haya alcanzado la posici�n final."
print "Recorrido: "+str(round(espacio,3))+"m / "+str(tiempo/FPS)+"s"
print "Error medio de la trayectoria: "+str(round(sum(\
    [distancia(trayectoria[i],trayectreal[i])\
    for i in range(len(trayectoria))])/tiempo,3))+"m"
raw_input()

