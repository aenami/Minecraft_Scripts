Todos estos scripts fueron creados en python y gracias al mod "Minescript". En este repositorio dejare varios de los scripts que vaya desarrollando para automatizar algunas tareas.

El scripts "Reolector_melones" y "Recolector_zanahorias" fueron creados y testeados dentro del servidor de hypixel en el garden. Para que estos funcionen correctamente se tienen que
utilizar ciertos bloques dentro de la plot donde se vaya a usar el script para que este funcione sin problemas.

Ambos scripts mencionados anteriormente tienen un sistema que previene que se queden atascados por cualquier motivo, este funciona en un hilo separado del proceso que lleva la recoleccion de los cultivos
se encarga de verificar que el jugador no se quede quieto por mas de un cierto tiempo, si eso sucede, resetea la posicion con ayuda del comando /Warp garden, este ultimo tiene que estar seteado en la posicion
donde el script comenzara a funcionar, esto para que al terminar todo el recorrido de recoleccion de la plot, se use este mismo script tanto para volver al inicio de este y repetir el ciclo de recoleccion,
como tambien para re posicionar al jugador ante un posible atasco detectado.

El script ha sido testeado con los siguientes valors de velocidad
-110 para el de recoleccion_zanahorias
-Maximo 400 para el de recoleccion_melones

A continuacion dejare el link de unos videos que muestran el funcionamiento del script de recolectar_melones:
https://youtu.be/oJFXID2rhYY
