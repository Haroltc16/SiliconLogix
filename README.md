# SiliconLogix
Sistema de inventarios

Primero descargar Visual Studio Code y descargar python con Workbench
Para lograr levantar el sistema se debe instalar python en el CMD y luego crear un paquete o archivo.

En el CMD crear un paquete y luego instalar una maquina virtual (VENV)
-- python -m venv venv  

Ingresar en a la carpeta en mención e instalar django

#LEVANTAR LA BASE DE DATOS
Para levantar la BD se debe migrar las clases creadas en la carpeta models.py se debe ejecutar:
-- py manage.py install mysqlclient
Para migrar se debe ejecutar:
-- python manage.py makemigrations
-- python manage.py migrate

#CREAR CARPETAS
Para crear carpetas se usa el siguiente comando
-- django-admin startproject Sistema . 

#LEVANTAR IMAGENES
Para la levantar el sistema con las imagenes se debe instalar Pillow:
-- python -m pip install Pillow  

#COMO CREAR UN SUPERUSUARIO
El superusuario se puede crear para cargar datos y administrar los datos directamente de Django
-- python manage.py createsuperuser





