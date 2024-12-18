
from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.http import Http404, HttpResponse
from django.views.decorators.cache import never_cache
from .models import Almacen, Categoria, Cliente, Inventario, Producto, Proveedor, Usuario, Venta
from .forms import LoginForm, VentaForm
from django.http import JsonResponse
from .models import Producto
from django.db.models import Count
from django.db.models import Sum
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from .models import Venta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
import json
from django.contrib import messages
from django.core.mail import EmailMessage
from django.core.mail import BadHeaderError
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Proveedor, Cliente, Usuario
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from django.http import HttpResponse
import os
from datetime import datetime
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import json

from django.contrib import messages
from Programa import models


# VISTAS PRINCIPALES.
def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect('login') 

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            dni = form.cleaned_data.get('username')  # Usando el campo 'dni' como username
            password = form.cleaned_data.get('password')
            
            # Autenticando al usuario
            user = authenticate(request, username=dni, password=password)

            if user is not None:
                # Loguear al usuario si las credenciales son válidas
                login(request, user)

                # Verificar a qué grupo pertenece el usuario y redirigir
                if user.groups.filter(name='Administrador').exists():
                    return redirect('admin_dashboard')
                elif user.groups.filter(name='Vendedor').exists():
                    return redirect('vendedor_dashboard')
                else:
                    return HttpResponse("El usuario no tiene un grupo asignado.")
            else:
                # Si la autenticación falla
                return render(request, 'login.html', {'form': form, 'error': 'DNI o contraseña incorrectos.'})
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})

#############################################################################

#VISTAS ADMINISTRADOR
@never_cache
@login_required
def admin_dashboard(request):
    return render(request, 'administrador/admin_dashboard.html')

def datos_productos_por_categoria(request):
    # Obtener la cantidad de productos por cada categoría
    datos = Producto.objects.values('categoria__nombre').annotate(total=Count('categoria'))
    return JsonResponse(list(datos), safe=False)

def datos_inventario_por_almacen(request):
    # Obtener la cantidad total de productos en cada almacén
    datos = Inventario.objects.values('almacen__nombre').annotate(total=Sum('cantidad'))
    return JsonResponse(list(datos), safe=False)

#ADMIN - CATEGORIA
def listar_categorias(request):
    query = request.GET.get('q')  # Obtiene el término de búsqueda desde el formulario
    if query:
        categorias = Categoria.objects.filter(nombre__icontains=query)  # Filtra por el nombre de la categoría
    else:
        categorias = Categoria.objects.all()  # Muestra todas las categorías si no hay búsqueda

    return render(request, 'administrador/categoria/categorias.html', {'categorias': categorias, 'query': query})

def registrar_categoria(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']

        Categoria.objects.create(nombre=nombre)
        
        return redirect('categorias')  # Redirige de nuevo a la lista de categorías después de registrar

    return render(request, 'administrador/categoria/registrar_categoria.html')

def actualizar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)

    if request.method == 'POST':
        categoria.nombre = request.POST['nombre']
        categoria.save()
        return redirect('categorias')

    return render(request, 'administrador/categoria/actualizar_categoria.html', {'categoria': categoria})

def eliminar_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, pk=categoria_id)
    categoria.delete()
    return redirect('categorias')

#ADMIN - PROVEEDOR
def listar_proveedores(request):
    query = request.GET.get('q')  # Obtiene el término de búsqueda desde el formulario
    if query:
        proveedores = Proveedor.objects.filter(nombre__icontains=query)  # Filtra por el nombre
    else:
        proveedores = Proveedor.objects.all()  # Muestra todos los proveedores si no hay búsqueda

    return render(request, 'administrador/proveedor/proveedores.html', {'proveedores': proveedores, 'query': query})

def eliminar_proveedor(request, ruc):
    proveedor = get_object_or_404(Proveedor, ruc=ruc)
    proveedor.delete()
    return redirect('proveedores')

def actualizar_proveedor(request, ruc):
    proveedor = get_object_or_404(Proveedor, ruc=ruc)

    if request.method == 'POST':
        proveedor.nombre = request.POST['nombre']
        proveedor.contacto = request.POST['contacto']
        proveedor.direccion = request.POST['direccion']
        proveedor.telefono = request.POST['telefono']
        
        nuevo_correo = request.POST['correo']
        
        # Validación de correo único (excluyendo el del proveedor actual)
        if Proveedor.objects.filter(correo=nuevo_correo).exclude(ruc=ruc).exists():
            messages.error(request, "El correo ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/proveedor/actualizar_proveedor.html', {'proveedor': proveedor})
        
        # Validación de formato de correo
        try:
            validate_email(nuevo_correo)
        except ValidationError:
            messages.error(request, "El formato del correo no es válido.")
            return render(request, 'administrador/proveedor/actualizar_proveedor.html', {'proveedor': proveedor})

        # Guardar el nuevo correo y demás datos del proveedor
        proveedor.correo = nuevo_correo
        proveedor.save()
        
        return redirect('proveedores')

    return render(request, 'administrador/proveedor/actualizar_proveedor.html', {'proveedor': proveedor})

def registrar_proveedor(request):
    if request.method == 'POST':
        ruc = request.POST['ruc']
        nombre = request.POST['nombre']
        contacto = request.POST['contacto']
        direccion = request.POST['direccion']
        telefono = request.POST['telefono']
        correo = request.POST['correo']

        # Validación de RUC único
        if Proveedor.objects.filter(ruc=ruc).exists():
            messages.error(request, "El RUC ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/proveedor/registrar_proveedor.html')

        # Validación de correo único
        if Proveedor.objects.filter(correo=correo).exists():
            messages.error(request, "El correo ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/proveedor/registrar_proveedor.html')

        # Validación de formato de correo
        try:
            validate_email(correo)
        except ValidationError:
            messages.error(request, "El formato del correo no es válido.")
            return render(request, 'administrador/proveedor/registrar_proveedor.html')

        # Crear el nuevo proveedor si pasa todas las validaciones
        Proveedor.objects.create(
            ruc=ruc,
            nombre=nombre,
            contacto=contacto,
            direccion=direccion,
            telefono=telefono,
            correo=correo
        )

        return redirect('proveedores')  # Redirige a la lista de proveedores después de registrar

    return render(request, 'administrador/proveedor/registrar_proveedor.html')

#ADMIN - PRODUCTO
def listar_productos(request):
    query = request.GET.get('q')  # Obtiene el término de búsqueda desde el formulario
    if query:
        productos = Producto.objects.filter(nombre__icontains=query)  # Filtra por el nombre del producto
    else:
        productos = Producto.objects.all()  # Muestra todos los productos si no hay búsqueda

    return render(request, 'administrador/productos/productos.html', {'productos': productos, 'query': query})

def registrar_producto(request):
    if request.method == 'POST':
        serie = request.POST['serie']
        nombre = request.POST['nombre']
        descripcion = request.POST.get('descripcion', '')
        precio = request.POST['precio']
        stock = request.POST['stock']
        categoria_id = request.POST['categoria']
        proveedor_ruc = request.POST['proveedor']

        # Validación de serie única
        if Producto.objects.filter(serie=serie).exists():
            messages.error(request, "La serie ya está en uso. Por favor, ingresa otra.")
            return render(request, 'administrador/productos/registrar_producto.html', {
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Validación de precio (debe ser un número positivo)
        try:
            precio = float(precio)
            if precio <= 0:
                messages.error(request, "El precio debe ser un número positivo.")
                return render(request, 'administrador/productos/registrar_producto.html', {
                    'categorias': Categoria.objects.all(),
                    'proveedores': Proveedor.objects.all()
                })
        except ValueError:
            messages.error(request, "El precio debe ser un número válido.")
            return render(request, 'administrador/productos/registrar_producto.html', {
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Validación de stock (debe ser un número entero no negativo)
        try:
            stock = int(stock)
            if stock < 0:
                messages.error(request, "El stock no puede ser negativo.")
                return render(request, 'administrador/productos/registrar_producto.html', {
                    'categorias': Categoria.objects.all(),
                    'proveedores': Proveedor.objects.all()
                })
        except ValueError:
            messages.error(request, "El stock debe ser un número entero válido.")
            return render(request, 'administrador/productos/registrar_producto.html', {
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Validación de la categoría y el proveedor
        try:
            categoria = Categoria.objects.get(pk=categoria_id)
        except Categoria.DoesNotExist:
            messages.error(request, "La categoría seleccionada no existe.")
            return render(request, 'administrador/productos/registrar_producto.html', {
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        try:
            proveedor = Proveedor.objects.get(ruc=proveedor_ruc)
        except Proveedor.DoesNotExist:
            messages.error(request, "El proveedor seleccionado no existe.")
            return render(request, 'administrador/productos/registrar_producto.html', {
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Crear el producto si pasa todas las validaciones
        Producto.objects.create(
            serie=serie,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            categoria=categoria,
            proveedor=proveedor
        )
        
        return redirect('productos')  # Redirige de nuevo a la lista de productos después de registrar

    # Obtener todas las categorías y proveedores para el formulario
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()
    return render(request, 'administrador/productos/registrar_producto.html', {'categorias': categorias, 'proveedores': proveedores})

def actualizar_producto(request, serie):
    # Obtener el producto con la serie proporcionada o retornar 404 si no existe
    producto = get_object_or_404(Producto, serie=serie)

    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre', producto.nombre).strip()
        producto.descripcion = request.POST.get('descripcion', producto.descripcion).strip()
        
        # Validación de precio (debe ser un número positivo)
        precio = request.POST.get('precio', producto.precio).strip()
        try:
            precio = float(precio)
            if precio <= 0:
                messages.error(request, "El precio debe ser un número positivo.")
                return render(request, 'administrador/productos/actualizar_producto.html', {
                    'producto': producto,
                    'categorias': Categoria.objects.all(),
                    'proveedores': Proveedor.objects.all()
                })
            producto.precio = precio
        except ValueError:
            messages.error(request, "El precio debe ser un número válido.")
            return render(request, 'administrador/productos/actualizar_producto.html', {
                'producto': producto,
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Validación de stock (debe ser un número entero no negativo)
        stock = request.POST.get('stock', producto.stock).strip()
        try:
            stock = int(stock)
            if stock < 0:
                messages.error(request, "El stock no puede ser negativo.")
                return render(request, 'administrador/productos/actualizar_producto.html', {
                    'producto': producto,
                    'categorias': Categoria.objects.all(),
                    'proveedores': Proveedor.objects.all()
                })
            producto.stock = stock
        except ValueError:
            messages.error(request, "El stock debe ser un número entero válido.")
            return render(request, 'administrador/productos/actualizar_producto.html', {
                'producto': producto,
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Validar y actualizar la categoría
        categoria_id = request.POST.get('categoria', producto.categoria.categoria_id).strip()
        try:
            categoria = Categoria.objects.get(pk=categoria_id)
            producto.categoria = categoria
        except Categoria.DoesNotExist:
            messages.error(request, "La categoría seleccionada no existe.")
            return render(request, 'administrador/productos/actualizar_producto.html', {
                'producto': producto,
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Validar y actualizar el proveedor
        proveedor_ruc = request.POST.get('proveedor', producto.proveedor.ruc).strip()
        try:
            proveedor = Proveedor.objects.get(ruc=proveedor_ruc)
            producto.proveedor = proveedor
        except Proveedor.DoesNotExist:
            messages.error(request, "El proveedor seleccionado no existe.")
            return render(request, 'administrador/productos/actualizar_producto.html', {
                'producto': producto,
                'categorias': Categoria.objects.all(),
                'proveedores': Proveedor.objects.all()
            })

        # Guardar los cambios en el producto si todas las validaciones pasan
        producto.save()
        return redirect('productos')  # Redirigir a la lista de productos

    # Obtener todas las categorías y proveedores para mostrar en el formulario
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()
    return render(request, 'administrador/productos/actualizar_producto.html', {
        'producto': producto,
        'categorias': categorias,
        'proveedores': proveedores
    })

def eliminar_producto(request, serie):
    producto = get_object_or_404(Producto, serie=serie)
    producto.delete()
    return redirect('productos')

#ADMIN - INVENTARIO
def inventario_view(request):
    query = request.GET.get('q')
    if query:
        inventario = Inventario.objects.filter(almacen__nombre__icontains=query)
    else:
        inventario = Inventario.objects.all()  # Obtiene todos los registros de inventario
        
    return render(request, 'administrador/inventario/inventario.html', {'inventario': inventario})

def producto_detalle(request, serie):
    producto = get_object_or_404(Producto, serie=serie)
    inventario = Inventario.objects.filter(producto=producto) \
                                   .values('almacen__nombre') \
                                   .annotate(total_cantidad=Sum('cantidad'))
    return render(request, 'administrador/inventario/producto_detalle.html', {'producto': producto, 'inventario': inventario})

def registrar_inventario(request):
    productos = Producto.objects.all()
    almacenes = Almacen.objects.all()

    if request.method == "POST":
        serie = request.POST.get('producto_serie')  # Cambia a producto_serie
        almacen_id = request.POST.get('almacen_id')  # Cambia a almacen_id
        cantidad = request.POST.get('cantidad')

        # Validar que los campos no estén vacíos
        if not serie or not almacen_id or not cantidad:
            return render(request, 'administrador/inventario/producto_almacen.html', {
                'productos': productos,
                'almacenes': almacenes,
                'error_message': 'Por favor, complete todos los campos.'
            })

        # Obtener el producto utilizando la serie
        try:
            producto = Producto.objects.get(serie=serie)
        except Producto.DoesNotExist:
            return render(request, 'administrador/inventario/producto_almacen.html', {
                'productos': productos,
                'almacenes': almacenes,
                'error_message': 'El producto con la serie proporcionada no existe.'
            })

        # Intentar crear el inventario
        try:
            Inventario.objects.create(producto=producto, almacen_id=almacen_id, cantidad=int(cantidad))
            return redirect('inventario')  # Cambia 'lista_inventario' por el nombre de la URL que maneja la lista de inventarios
        except Exception as e:
            return render(request, 'administrador/inventario/producto_almacen.html', {
                'productos': productos,
                'almacenes': almacenes,
                'error_message': f'Error al registrar el inventario: {str(e)}'
            })

    context = {
        'productos': productos,
        'almacenes': almacenes,
    }
    return render(request, 'administrador/inventario/producto_almacen.html', context) 

#ADMIN - CLIENTE
def listar_clientes(request):
    query = request.GET.get('q')
    if query:
        clientes = Cliente.objects.filter(nombre__icontains=query)
    else:
        clientes = Cliente.objects.all()

    return render(request, 'administrador/cliente/clientes.html', {'clientes': clientes, 'query': query})

def eliminar_cliente(request, dni):
    cliente = get_object_or_404(Cliente, dni=dni)
    cliente.delete()
    return redirect('clientes')

def actualizar_cliente(request, dni):
    cliente = get_object_or_404(Cliente, dni=dni)

    if request.method == 'POST':
        cliente.nombre = request.POST['nombre']
        cliente.apellido = request.POST['apellido']
        cliente.direccion = request.POST['direccion']
        cliente.telefono = request.POST['telefono']
        nuevo_correo = request.POST['correo']

        # Validación de correo único (excepto para el mismo cliente)
        if Cliente.objects.filter(correo=nuevo_correo).exclude(dni=dni).exists():
            messages.error(request, "El correo ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/cliente/actualizar_cliente.html', {'cliente': cliente})

        # Validación de formato de correo
        try:
            validate_email(nuevo_correo)
        except ValidationError:
            messages.error(request, "El formato del correo no es válido.")
            return render(request, 'administrador/cliente/actualizar_cliente.html', {'cliente': cliente})

        # Actualizar los datos del cliente
        cliente.correo = nuevo_correo
        cliente.save()
        return redirect('clientes')

    return render(request, 'administrador/cliente/actualizar_cliente.html', {'cliente': cliente})

def registrar_cliente(request):
    if request.method == 'POST':
        dni = request.POST['dni']
        nombre = request.POST['nombre']
        apellido = request.POST['apellido']
        telefono = request.POST['telefono']
        direccion = request.POST['direccion']
        correo = request.POST['correo']
        
        # Validación de DNI único
        if Cliente.objects.filter(dni=dni).exists():
            messages.error(request, "El DNI ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/cliente/registrar_cliente.html')
        
        # Validación de correo único
        if Cliente.objects.filter(correo=correo).exists():
            messages.error(request, "El correo ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/cliente/registrar_cliente.html')
        
        # Validación de formato de correo
        try:
            validate_email(correo)
        except ValidationError:
            messages.error(request, "El formato del correo no es válido.")
            return render(request, 'administrador/cliente/registrar_cliente.html')

        # Crear el cliente si todas las validaciones son exitosas
        Cliente.objects.create(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            correo=correo
        )
        
        return redirect('clientes')  # Redirige a la lista de clientes después de registrar

    return render(request, 'administrador/cliente/registrar_cliente.html')
#ADMIN - PRODUCTIVIDAD

#ADMIN - VENTAS

def ventas_grafico(request):
    # Agrupa las ventas por fecha
    ventas = Venta.objects.all()
    ventas_por_dia = {}

    for venta in ventas:
        fecha = venta.fecha_venta
        total_venta = float(venta.total())  # Convierte el total a float

        if fecha in ventas_por_dia:
            ventas_por_dia[fecha] += total_venta
        else:
            ventas_por_dia[fecha] = total_venta

    # Convertir las fechas y montos a listas para JavaScript
    fechas = [fecha.strftime('%Y-%m-%d') for fecha in sorted(ventas_por_dia.keys())]
    montos = [ventas_por_dia[fecha] for fecha in sorted(ventas_por_dia.keys())]

    context = {
        'fechas': json.dumps(fechas),  # Convierte a JSON
        'montos': json.dumps(montos)   # Convierte a JSON
    }
    return render(request, 'administrador/inventario/inventario.html', context)

def obtener_ventas(request):
    # Agrupa las ventas por fecha y cuenta cuántas ventas hay por cada fecha
    ventas = Venta.objects.values('fecha_venta').annotate(cantidad=Count('id'))

    # Formato de salida para el gráfico
    fechas = [venta['fecha_venta'].strftime('%Y-%m-%d') for venta in ventas]
    cantidades = [venta['cantidad'] for venta in ventas]

    # Pasar datos al contexto para el renderizado
    context = {
        'fechas': json.dumps(fechas),  # Convierte a JSON
        'cantidades': json.dumps(cantidades)  # Convierte a JSON
    }
    return render(request, 'administrador/inventario/inventario.html', context)

def registrar_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('ventas')  # Redirige al dashboard después de registrar la venta
    else:
        form = VentaForm()
    return render(request, 'administrador/ventas/registrar_ventas.html', {'form': form})

def listar_ventas(request):
    ventas = Venta.objects.all().order_by('-fecha_venta')  # Ordena las ventas por fecha
    return render(request, 'administrador/ventas/ventas.html', {'ventas': ventas})

def actualizar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            return redirect('ventas')
    else:
        form = VentaForm(instance=venta)
    return render(request, 'ventas/actualizar_venta.html', {'form': form})

def eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    venta.delete()
    return redirect('ventas')

#ADMIN - USUARIOS
def listar_usuarios(request):
    query = request.GET.get('q')  # Obtiene el término de búsqueda desde el formulario
    if query:
        usuarios = Usuario.objects.filter(nombre__icontains=query)  # Filtra por el nombre
    else:
        usuarios = Usuario.objects.all()  # Muestra todos los usuarios si no hay búsqueda

    return render(request, 'administrador/usuario/usuarios.html', {'usuarios': usuarios, 'query': query})

def eliminar_usuario(request, dni):
    usuario = get_object_or_404(Usuario, dni=dni)
    usuario.delete()
    return redirect('usuarios')

# def actualizar_usuario(request, dni):
#     usuario = get_object_or_404(Usuario, dni=dni)

#     if request.method == 'POST':
#         usuario.nombre = request.POST['nombre']
#         usuario.apellidos = request.POST['apellidos']
#         usuario.correo = request.POST['correo']
#         usuario.telefono = request.POST['telefono']
#         usuario.edad = request.POST['edad']

#         # Actualizar la contraseña si se proporciona una nueva
#         nueva_contraseña = request.POST.get('password')
#         if nueva_contraseña:
#             usuario.set_password(nueva_contraseña)

#         # Actualizar el grupo del usuario
#         grupo_nombre = request.POST.get('grupo', None)
#         if grupo_nombre:
#             try:
#                 grupo = Group.objects.get(name=grupo_nombre)
#                 usuario.groups.clear()
#                 usuario.groups.add(grupo)
#             except Group.DoesNotExist:
#                 pass
            
#         if 'foto' in request.FILES:
#             usuario.foto = request.FILES['foto']
            
#         usuario.save()
#         return redirect('usuarios')

#     # Pasar los grupos disponibles a la plantilla
#     grupos_disponibles = Group.objects.all()
#     return render(request, 'administrador/usuario/actualizar_usuario.html', {
#         'usuario': usuario,
#         'grupos': grupos_disponibles
#     })
    
def actualizar_usuario(request, dni):
    usuario = get_object_or_404(Usuario, dni=dni)

    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.POST['nombre']
        apellidos = request.POST['apellidos']
        correo = request.POST['correo']
        telefono = request.POST['telefono']
        edad = request.POST['edad']

        # Validación de correo único
        if Usuario.objects.filter(correo=correo).exclude(dni=dni).exists():
            messages.error(request, "El correo ya está en uso. Por favor, ingresa otro.")
            grupos_disponibles = Group.objects.all()
            return render(request, 'administrador/usuario/actualizar_usuario.html', {
                'usuario': usuario,
                'grupos': grupos_disponibles
            })

        # Actualizar los datos del usuario
        usuario.nombre = nombre
        usuario.apellidos = apellidos
        usuario.correo = correo
        usuario.telefono = telefono
        usuario.edad = edad

        # Actualizar la contraseña si se proporciona una nueva
        nueva_contraseña = request.POST.get('password')
        if nueva_contraseña:
            usuario.set_password(nueva_contraseña)

        # Validar si el archivo es una imagen antes de actualizar la foto
        foto = request.FILES.get('foto')
        if foto:
            if not foto.content_type.startswith('image/'):
                messages.error(request, "Solo se permiten archivos de imagen (JPEG, PNG, GIF, etc.).")
                grupos_disponibles = Group.objects.all()
                return render(request, 'administrador/usuario/actualizar_usuario.html', {
                    'usuario': usuario,
                    'grupos': grupos_disponibles
                })
            usuario.foto = foto

        # Actualizar el grupo del usuario
        grupo_nombre = request.POST.get('grupo', None)
        if grupo_nombre:
            try:
                grupo = Group.objects.get(name=grupo_nombre)
                usuario.groups.clear()  # Limpiar los grupos actuales
                usuario.groups.add(grupo)  # Asignar el nuevo grupo
            except Group.DoesNotExist:
                pass

        # Guardar los cambios
        usuario.save()
        return redirect('usuarios')

    # Pasar los grupos disponibles a la plantilla
    grupos_disponibles = Group.objects.all()
    return render(request, 'administrador/usuario/actualizar_usuario.html', {
        'usuario': usuario,
        'grupos': grupos_disponibles
    })

def detalles_usuario(request, dni):
    usuario = get_object_or_404(Usuario, dni=dni)
    return render(request, 'administrador/usuario/detalles_usuario.html', {'usuario': usuario})

# def registrar_usuario(request):
#     if request.method == 'POST':
#         # Obtener los datos del formulario
#         dni = request.POST['dni']
#         nombre = request.POST['nombre']
#         apellidos = request.POST['apellidos']
#         correo = request.POST['correo']
#         telefono = request.POST['telefono']
#         cargo = request.POST['cargo']
#         area = request.POST['area']
#         edad = request.POST['edad']
#         password = request.POST['password']
        
#         # Obtener el archivo de imagen
#         foto = request.FILES.get('foto')  # Capturar el archivo de imagen

#         # Obtener el nombre del grupo seleccionado, si existe
#         grupo_nombre = request.POST.get('grupo', None)
        
#         # Crear el usuario usando el manager
#         usuario = Usuario.objects.create_user(
#             dni=dni,
#             nombre=nombre,
#             apellidos=apellidos,
#             correo=correo,
#             telefono=telefono,
#             cargo=cargo,
#             area=area,
#             edad=edad,
#             password=password
#         )

#         # Asignar grupo al usuario si se seleccionó uno
#         if grupo_nombre:
#             try:
#                 grupo = Group.objects.get(name=grupo_nombre)
#                 usuario.groups.add(grupo)
#                 # Si el grupo es "Administradores", establecer el usuario como administrador
#                 if grupo_nombre == 'Administradores':
#                     usuario.is_admin = True
#                     usuario.is_staff = True
#                     usuario.is_superuser = True
#                     usuario.save()
#             except Group.DoesNotExist:
#                 pass

#         # Redirigir a la lista de usuarios después de guardar
#         return redirect('usuarios')

#     # Obtener los grupos disponibles para mostrarlos en el formulario
#     grupos_disponibles = Group.objects.all()
#     return render(request, 'administrador/usuario/registrar_usuario.html', {
#         'grupos': grupos_disponibles
#     })

def registrar_usuario(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        dni = request.POST['dni']
        nombre = request.POST['nombre']
        apellidos = request.POST['apellidos']
        correo = request.POST['correo']
        telefono = request.POST['telefono']
        edad = request.POST['edad']
        password = request.POST['password']
        
        # Validación de DNI único
        if Usuario.objects.filter(dni=dni).exists():
            messages.error(request, "El DNI ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/usuario/registrar_usuario.html', {'grupos': Group.objects.all()})
        
                
        # Validación de correo único
        if Usuario.objects.filter(correo=correo).exists():
            messages.error(request, "El correo ya está en uso. Por favor, ingresa otro.")
            return render(request, 'administrador/usuario/registrar_usuario.html', {'grupos': Group.objects.all()})
        
        # Validar si el archivo es una imagen
        foto = request.FILES.get('foto')
        if foto:
            if not foto.content_type.startswith('image/'):
                messages.error(request, "Solo se permiten archivos de imagen (JPEG, PNG, GIF, etc.).")
                return render(request, 'administrador/usuario/registrar_usuario.html', {'grupos': Group.objects.all()})
            
        # Obtener el archivo de imagen
        foto = request.FILES.get('foto')  # Capturar el archivo de imagen

        # Crear el nuevo usuario con la contraseña encriptada
        usuario = Usuario.objects.create(
            dni=dni,
            nombre=nombre,
            apellidos=apellidos,
            correo=correo,
            telefono=telefono,
            edad=edad,
            password=make_password(password),  # Encriptar la contraseña
            foto=foto  # Guardar la foto en el modelo
        )

        # Asignar grupo al usuario si se seleccionó uno
        grupo_nombre = request.POST.get('grupo', None)
        if grupo_nombre:
            try:
                grupo = Group.objects.get(name=grupo_nombre)
                usuario.groups.add(grupo)
            except Group.DoesNotExist:
                pass

        # Guardar el usuario y redirigir a la lista de usuarios
        usuario.save()
        return redirect('usuarios')

    # Obtener los grupos disponibles para mostrarlos en el formulario
    grupos_disponibles = Group.objects.all()
    return render(request, 'administrador/usuario/registrar_usuario.html', {
        'grupos': grupos_disponibles
    })
    

##############################################################################

#VISTAS VENDEDOR

@never_cache
@login_required
def vendedor_dashboard(request):
    return render(request, 'vendedor/vendedor_dashboard.html')

#VENDEDOR - CATEGORIA

#VENDEDOR - PROVEEDOR
def v_listar_proveedores(request):
    query = request.GET.get('q')  # Obtiene el término de búsqueda desde el formulario
    if query:
        proveedores = Proveedor.objects.filter(nombre__icontains=query)  # Filtra por el nombre
    else:
        proveedores = Proveedor.objects.all()  # Muestra todos los proveedores si no hay búsqueda

    return render(request, 'vendedor/proveedor/v_proveedores.html', {'proveedores': proveedores, 'query': query})

def v_eliminar_proveedor(request, ruc):
    proveedor = get_object_or_404(Proveedor, ruc=ruc)
    proveedor.delete()
    return redirect('v_proveedores')

def v_actualizar_proveedor(request, ruc):
    proveedor = get_object_or_404(Proveedor, ruc=ruc)

    if request.method == 'POST':
        proveedor.nombre = request.POST['nombre']
        proveedor.contacto = request.POST['contacto']
        proveedor.direccion = request.POST['direccion']
        proveedor.telefono = request.POST['telefono']
        proveedor.correo = request.POST['correo']
        proveedor.save()
        return redirect('v_proveedores')

    return render(request, 'vendedor/proveedor/v_actualizar_proveedor.html', {'proveedor': proveedor})

def v_registrar_proveedor(request):
    if request.method == 'POST':
        ruc = request.POST['ruc']
        nombre = request.POST['nombre']
        contacto = request.POST['contacto']
        direccion = request.POST['direccion']
        telefono = request.POST['telefono']
        correo = request.POST['correo']
        
        Proveedor.objects.create(
            ruc=ruc,
            nombre=nombre,
            contacto=contacto,
            direccion=direccion,
            telefono=telefono,
            correo=correo
        )
        
        return redirect('v_proveedores')  # Redirige de nuevo a la lista de proveedores después de registrar
        
    return render(request, 'vendedor/proveedor/v_registrar_proveedor.html')

#VENDEDOR - PRODUCTO

def v_listar_productos(request):
    query = request.GET.get('q')  # Obtiene el término de búsqueda desde el formulario
    if query:
        productos = Producto.objects.filter(nombre__icontains=query)  # Filtra por el nombre del producto
    else:
        productos = Producto.objects.all()  # Muestra todos los productos si no hay búsqueda

    return render(request, 'vendedor/productos/v_productos.html', {'productos': productos, 'query': query})

def v_registrar_producto(request):
    if request.method == 'POST':
        serie = request.POST['serie']
        nombre = request.POST['nombre']
        descripcion = request.POST.get('descripcion', '')
        precio = request.POST['precio']
        stock = request.POST['stock']
        categoria_id = request.POST['categoria']
        proveedor_ruc = request.POST['proveedor']

        # Validación de la categoría y el proveedor
        try:
            categoria = Categoria.objects.get(pk=categoria_id)
        except Categoria.DoesNotExist:
            raise Http404("La categoría seleccionada no existe.")

        try:
            proveedor = Proveedor.objects.get(ruc=proveedor_ruc)
        except Proveedor.DoesNotExist:
            raise Http404("El proveedor seleccionado no existe.")

        # Crear el producto si la categoría y el proveedor son válidos
        Producto.objects.create(
            serie=serie,
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            categoria=categoria,
            proveedor=proveedor
        )
        
        return redirect('v_productos')  # Redirige de nuevo a la lista de productos después de registrar

    # Obtener todas las categorías y proveedores para el formulario
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()
    return render(request, 'vendedor/productos/v_registrar_producto.html', {'categorias': categorias, 'proveedores': proveedores})

def v_actualizar_producto(request, serie):
    # Obtener el producto con la serie proporcionada o retornar 404 si no existe
    producto = get_object_or_404(Producto, serie=serie)

    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre', producto.nombre).strip()
        producto.descripcion = request.POST.get('descripcion', producto.descripcion).strip()
        producto.precio = request.POST.get('precio', producto.precio).strip()
        producto.stock = request.POST.get('stock', producto.stock).strip()
        categoria_id = request.POST.get('categoria', producto.categoria.categoria_id).strip()
        proveedor_ruc = request.POST.get('proveedor', producto.proveedor.ruc).strip()

        # Validar y actualizar la categoría
        try:
            categoria = Categoria.objects.get(pk=categoria_id)
            producto.categoria = categoria
        except Categoria.DoesNotExist:
            raise Http404("La categoría seleccionada no existe.")

        # Validar y actualizar el proveedor
        try:
            proveedor = Proveedor.objects.get(ruc=proveedor_ruc)
            producto.proveedor = proveedor
        except Proveedor.DoesNotExist:
            raise Http404("El proveedor seleccionado no existe.")

        # Guardar los cambios en el producto
        producto.save()
        return redirect('v_productos')  # Redirigir a la lista de productos

    # Obtener todas las categorías y proveedores para mostrar en el formulario
    categorias = Categoria.objects.all()
    proveedores = Proveedor.objects.all()
    return render(request, 'vendedor/productos/v_actualizar_producto.html', {
        'producto': producto,
        'categorias': categorias,
        'proveedores': proveedores
    })

def v_eliminar_producto(request, serie):
    producto = get_object_or_404(Producto, serie=serie)
    producto.delete()
    return redirect('v_productos')

#VENDEDOR - ALMACEN

#VENDEDOR - INVENTARIO

def v_inventario_view(request):
    query = request.GET.get('q')
    if query:
        inventario = Inventario.objects.filter(almacen__nombre__icontains=query)
    else:
        inventario = Inventario.objects.all()  # Obtiene todos los registros de inventario
        
    return render(request, 'vendedor/inventario/v_inventario.html', {'inventario': inventario})

def v_producto_detalle(request, serie):
    producto = get_object_or_404(Producto, serie=serie)
    inventario = Inventario.objects.filter(producto=producto) \
                                   .values('almacen__nombre') \
                                   .annotate(total_cantidad=Sum('cantidad'))
    return render(request, 'vendedor/inventario/v_producto_detalle.html', {'producto': producto, 'inventario': inventario})

def v_registrar_inventario(request):
    productos = Producto.objects.all()
    almacenes = Almacen.objects.all()

    if request.method == "POST":
        serie = request.POST.get('producto_serie')  # Cambia a producto_serie
        almacen_id = request.POST.get('almacen_id')  # Cambia a almacen_id
        cantidad = request.POST.get('cantidad')

        # Validar que los campos no estén vacíos
        if not serie or not almacen_id or not cantidad:
            return render(request, 'vendedor/inventario/v_producto_almacen.html', {
                'productos': productos,
                'almacenes': almacenes,
                'error_message': 'Por favor, complete todos los campos.'
            })

        # Obtener el producto utilizando la serie
        try:
            producto = Producto.objects.get(serie=serie)
        except Producto.DoesNotExist:
            return render(request, 'vendedor/inventario/v_producto_almacen.html', {
                'productos': productos,
                'almacenes': almacenes,
                'error_message': 'El producto con la serie proporcionada no existe.'
            })

        # Intentar crear el inventario
        try:
            Inventario.objects.create(producto=producto, almacen_id=almacen_id, cantidad=int(cantidad))
            return redirect('v_inventario')  # Cambia 'lista_inventario' por el nombre de la URL que maneja la lista de inventarios
        except Exception as e:
            return render(request, 'vendedor/inventario/v_producto_almacen.html', {
                'productos': productos,
                'almacenes': almacenes,
                'error_message': f'Error al registrar el inventario: {str(e)}'
            })

    context = {
        'productos': productos,
        'almacenes': almacenes,
    }
    return render(request, 'vendedor/inventario/v_producto_almacen.html', context)

#VENDEDOR - CLIENTE
def v_listar_clientes(request):
    query = request.GET.get('q')
    if query:
        clientes = Cliente.objects.filter(nombre__icontains=query)
    else:
        clientes = Cliente.objects.all()

    return render(request, 'vendedor/cliente/v_clientes.html', {'clientes': clientes, 'query': query})

def v_eliminar_cliente(request, dni):
    cliente = get_object_or_404(Cliente, dni=dni)
    cliente.delete()
    return redirect('v_clientes')

def v_actualizar_cliente(request, dni):
    cliente = get_object_or_404(Cliente, dni=dni)

    if request.method == 'POST':
        cliente.nombre = request.POST['nombre']
        cliente.apellido = request.POST['apellido']
        cliente.direccion = request.POST['direccion']
        cliente.telefono = request.POST['telefono']
        cliente.correo = request.POST['correo']
        cliente.save()
        return redirect('v_clientes')

    return render(request, 'vendedor/cliente/v_actualizar_cliente.html', {'cliente': cliente})

def v_registrar_cliente(request):
    if request.method == 'POST':
        dni = request.POST['dni']
        nombre = request.POST['nombre']
        apellido =request.POST['apellido']
        telefono = request.POST['telefono']
        direccion = request.POST['direccion']
        correo = request.POST['correo']
        
        Cliente.objects.create(
            dni=dni,
            nombre=nombre,
            apellido=apellido,
            telefono=telefono,
            direccion=direccion,
            correo=correo
        )
        
        return redirect('v_clientes')  # Redirige de nuevo a la lista de clientes después de registrar
        
    return render(request, 'vendedor/cliente/v_registrar_cliente.html')

#VENDEDOR - PRODUCTIVIDAD

#VENDEDOR - VENTAS

def v_ventas_grafico(request):
    # Agrupa las ventas por fecha
    ventas = Venta.objects.all()
    ventas_por_dia = {}

    for venta in ventas:
        fecha = venta.fecha_venta
        total_venta = float(venta.total())  # Convierte el total a float

        if fecha in ventas_por_dia:
            ventas_por_dia[fecha] += total_venta
        else:
            ventas_por_dia[fecha] = total_venta

    # Convertir las fechas y montos a listas para JavaScript
    fechas = [fecha.strftime('%Y-%m-%d') for fecha in sorted(ventas_por_dia.keys())]
    montos = [ventas_por_dia[fecha] for fecha in sorted(ventas_por_dia.keys())]

    context = {
        'fechas': json.dumps(fechas),  # Convierte a JSON
        'montos': json.dumps(montos)   # Convierte a JSON
    }
    return render(request, 'vendedor/inventario/v_inventario.html', context)

def v_obtener_ventas(request):
    # Agrupa las ventas por fecha y cuenta cuántas ventas hay por cada fecha
    ventas = Venta.objects.values('fecha_venta').annotate(cantidad=Count('id'))

    # Formato de salida para el gráfico
    fechas = [venta['fecha_venta'].strftime('%Y-%m-%d') for venta in ventas]
    cantidades = [venta['cantidad'] for venta in ventas]

    # Pasar datos al contexto para el renderizado
    context = {
        'fechas': json.dumps(fechas),  # Convierte a JSON
        'cantidades': json.dumps(cantidades)  # Convierte a JSON
    }
    return render(request, 'vendedor/inventario/v_inventario.html', context)

def v_registrar_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('v_ventas')  # Redirige al dashboard después de registrar la venta
    else:
        form = VentaForm()
    return render(request, 'vendedor/ventas/v_registrar_ventas.html', {'form': form})

def v_listar_ventas(request):
    ventas = Venta.objects.all().order_by('-fecha_venta')  # Ordena las ventas por fecha
    return render(request, 'vendedor/ventas/v_ventas.html', {'ventas': ventas})

def v_actualizar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    if request.method == 'POST':
        form = VentaForm(request.POST, instance=venta)
        if form.is_valid():
            form.save()
            return redirect('v_ventas')
    else:
        form = VentaForm(instance=venta)
    return render(request, 'vendedor/ventas/v_actualizar_venta.html', {'form': form})

def v_eliminar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    venta.delete()
    return redirect('v_ventas')


###############################################################################

##reportes
# Generar y guardar el PDF de ventas
def reporte_ventas_pdf(request):
    # Crear la respuesta HTTP con tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_ventas.pdf"'

    # Configurar el documento PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    elementos = []

    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título principal
    titulo_style = ParagraphStyle(
        'TituloStyle',
        parent=styles['Title'],
        fontSize=16,
        alignment=1,  # Centrado
        spaceAfter=12
    )
    #informacion de la empresa
    elementos.append(Paragraph("DIRECCION : Jr moquegua 734   JUNIN-HUANCAYO-HUANCAYO"))
    elementos.append(Paragraph("TELEFONO : 965650117"))
    elementos.append(Paragraph("RUC : 20487151921"))
    elementos.append(Paragraph("_"))
    elementos.append(Paragraph("_"))
    
    # Fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Logo de la empresa
    logo_path = os.path.join('Programa/static/img', 'logo_logix.png')
    
    # Fecha
    elementos.append(Paragraph(f"FECHA DE REPORTE: {fecha_actual}", styles['Normal']))
    elementos.append(Spacer(1, 12))  # Espacio en blanco
    elementos.append(Spacer(1, 12))  # Espacio en blanco

    # Agregar elementos al documento
    # Título principal
    elementos.append(Paragraph("Reporte de Ventas", titulo_style))

    # Datos de la tabla
    ventas = Venta.objects.all()
    datos_tabla = [
        ['Cliente', 'Producto', 'Cantidad', 'Fecha de Venta', 'Total']
    ]

    for venta in ventas:
        datos_tabla.append([
            venta.cliente.nombre,
            venta.producto.nombre,
            str(venta.cantidad),
            str(venta.fecha_venta),
            f"S/. {venta.total():.2f}"
        ])

    # Crear tabla con estilo
    tabla = Table(datos_tabla)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.beige),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    elementos.append(tabla)

    # Pie de página con número de página
    def pie_pagina(canvas, doc):
        canvas.saveState()
        
        # Agregar logo en la esquina superior derecha
        try:
            logo = Image(logo_path, width=2*inch, height=0.7*inch)
            logo.drawOn(canvas, letter[0]-2.5*inch, letter[1]-1*inch)
        except Exception as e:
            print(f"Error al cargar el logo: {e}")
        
        # Número de página en la parte inferior
        canvas.setFont('Helvetica', 10)
        canvas.drawString(inch, 0.75 * inch, f"Página {doc.page}")
        canvas.restoreState()

    # Construir el PDF
    doc.build(elementos, onFirstPage=pie_pagina, onLaterPages=pie_pagina)

    return response

# Generar y guardar el PDF de productos
def reporte_productos_pdf(request):
    # Crear el objeto HttpResponse con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_almacenes.pdf"'

    # Crear el objeto Canvas de ReportLab
    pdf = canvas.Canvas(response, pagesize=letter)
    ancho, alto = letter

    pdf.drawString(35, alto - 60, "DIRECCIONES : Jr moquegua 734   JUNIN-HUANCAYO-HUANCAYO")  # Ajustamos la coordenada Y
    pdf.drawString(35, alto - 75, "TELEFONO : 965650117")  # Ajustamos la coordenada Y
    pdf.drawString(35, alto - 90, "RUC : 20487151921")  # Ajustamos la coordenada Y

    # Fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(35, alto - 45, f"FECHA DE REPORTE: {fecha_actual}")

    # Logo de la empresa
    logo_path = os.path.join('Programa/static/img', 'logo_logix.png')
    try:
        pdf.drawImage(logo_path, ancho - 2.5 * inch, alto - 1.3 * inch, width=2 * inch, height=0.7 * inch, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar el logo: {e}")

    # Título del reporte
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, alto - 120, "Reporte de Almacenes")  # Ajustamos la coordenada Y

    y = alto - 170  # Posición inicial

    # Obtener los datos de los almacenes
    almacenes = Almacen.objects.all()

    for almacen in almacenes:
        # Mostrar el nombre del almacén
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"Almacén: {almacen.nombre}")
        y -= 20

        # Obtener todos los productos relacionados con inventarios del almacén
        inventarios = Inventario.objects.filter(almacen=almacen)
        productos_ids = inventarios.values_list('producto_id', flat=True)
        productos = Producto.objects.filter(serie__in=productos_ids)

        # Si no hay productos, mostrar mensaje
        if not productos.exists():
            pdf.setFont("Helvetica-Oblique", 12)
            pdf.drawString(70, y, "No hay productos registrados.")
            y -= 20
            continue

        # Encabezados de la tabla
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(70, y, "Producto")
        pdf.drawString(300, y, "Cantidad Total")
        pdf.drawString(410, y, "Proveedor")
        y -= 20

        # Datos de los productos agrupados
        pdf.setFont("Helvetica", 12)
        for producto in productos:
            cantidad_total = inventarios.filter(producto=producto).aggregate(Sum('cantidad'))['cantidad__sum'] or 0
            proveedor = producto.proveedor.nombre if producto.proveedor else "Ninguno"

            # Mostrar los datos del producto
            pdf.drawString(70, y, str(producto.nombre))
            pdf.drawString(330, y, str(cantidad_total))
            pdf.drawString(420, y, proveedor)
            y -= 20

            # Si la página se llena, añadir una nueva página
            if y < 90:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                pdf.drawString(50, alto - 50, f"Fecha de Reporte: {fecha_actual}")
                try:
                    pdf.drawImage(logo_path, ancho - 2.5 * inch, alto - 1.3 * inch, width=2 * inch, height=0.7 * inch, preserveAspectRatio=True)
                except Exception as e:
                    print(f"Error al cargar el logo en la nueva página: {e}")
                y = alto - 120
                pdf.setFont("Helvetica-Bold", 16)
                pdf.drawString(200, alto - 120, "Reporte de Almacenes")

        # Espacio entre almacenes
        y -= 20

    # Finalizar el documento PDF
    pdf.showPage()
    pdf.save()
    return response

# Generar y guardar el PDF de cliente
def reporte_clientes_pdf(request):
    # Crear el objeto HttpResponse con el tipo de contenido PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_clientes.pdf"'

    # Crear el objeto Canvas de ReportLab
    pdf = canvas.Canvas(response, pagesize=letter)
    ancho, alto = letter

    # Fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(35, alto - 50, f"FECHA DE REPORTE: {fecha_actual}")

    #INFORMACION DE LA EMPRESA
    pdf.drawString(35, alto - 65, "DIRECCIONES : Jr moquegua 734   JUNIN-HUANCAYO-HUANCAYO")
    pdf.drawString(35, alto - 80, "TELEFONO : 965650117")
    pdf.drawString(35, alto - 95, "RUC : 20487151921")
    
    # Logo de la empresa
    logo_path = os.path.join('Programa/static/img', 'logo_logix.png')
    try:
        pdf.drawImage(logo_path, ancho - 2.5 * inch, alto - 1.5 * inch, width=2 * inch, height=0.7 * inch, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar el logo: {e}")

    # Título del reporte
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, alto - 120, "Reporte de Clientes")

    y = alto - 150  # Posición inicial

    # Obtener todos los clientes
    clientes = Cliente.objects.all()

    for cliente in clientes:
        # Información del cliente
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"Cliente: {cliente.nombre} {cliente.apellido or ''}")
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y - 20, f"DNI: {cliente.dni}")
        pdf.drawString(200, y - 20, f"Teléfono: {cliente.telefono or 'N/A'}")
        pdf.drawString(400, y - 20, f"Correo: {cliente.correo or 'N/A'}")
        y -= 40

        # Mostrar encabezado de la tabla de compras
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(70, y, "Producto")
        pdf.drawString(320, y, "Cantidad")
        pdf.drawString(390, y, "Precio Total")
        pdf.drawString(480, y, "Fecha de Compra")
        y -= 20

        # Obtener los productos comprados por el cliente a través de las ventas
        ventas = Venta.objects.filter(cliente=cliente)

        if not ventas.exists():
            pdf.setFont("Helvetica-Oblique", 12)
            pdf.drawString(70, y, "No hay compras registradas para este cliente.")
            y -= 20
            continue

        # Detalles de las compras
        for venta in ventas:
            producto = venta.producto
            cantidad = venta.cantidad
            precio_total = cantidad * producto.precio
            fecha_compra = venta.fecha_venta.strftime("%d/%m/%Y")  # Formato de fecha

            # Mostrar datos de la compra
            pdf.drawString(70, y, producto.nombre)
            pdf.drawString(350, y, str(cantidad))
            pdf.drawString(400, y, f"S/. {precio_total:.2f}")
            pdf.drawString(500, y, fecha_compra)
            y -= 20

            # Añadir nueva página si es necesario
            if y < 90:
                pdf.showPage()
                pdf.setFont("Helvetica-Bold", 14)
                pdf.drawString(200, alto - 100, "Reporte de Clientes")
                pdf.setFont("Helvetica", 12)
                pdf.drawString(50, alto - 50, f"Fecha de Reporte: {fecha_actual}")
                try:
                    pdf.drawImage(logo_path, ancho - 2.5 * inch, alto - 1.5 * inch, width=2 * inch, height=0.7 * inch, preserveAspectRatio=True)
                except Exception as e:
                    print(f"Error al cargar el logo en la nueva página: {e}")
                y = alto - 150

        # Espacio entre clientes
        y -= 20

    # Finalizar el PDF
    pdf.showPage()
    pdf.save()
    return response

# Función para generar reporte de proveedores
def reporte_proveedores(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_proveedores.pdf"'  # Mostrar en navegador

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    ancho, height = letter

    # Fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(35, height - 40, f"FECHA DE REPORTE: {fecha_actual}")

    #INFORMACION DE LA EMPRESA
    pdf.drawString(35, height - 55, "DIRECCIONES : Jr moquegua 734   JUNIN-HUANCAYO-HUANCAYO")
    pdf.drawString(35, height - 70, "TELEFONO : 965650117")
    pdf.drawString(35, height - 85, "RUC : 20487151921")

    # Logo de la empresa
    logo_path = os.path.join('Programa/static/img', 'logo_logix.png')
    try:
        pdf.drawImage(logo_path, ancho - 2.5 * inch, height - 1.5 * inch, width=2 * inch, height=0.7 * inch, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar el logo: {e}")
        
    # Encabezado del reporte
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 130, "Reporte de Proveedores")
    pdf.setFont("Helvetica", 12)

    y = height - 180  # Espaciado inicial

    # Iterar sobre los proveedores
    for proveedor in Proveedor.objects.all():
        if y < 100:  # Crear nueva página si no hay espacio
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 12)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, proveedor.nombre)
        y -= 20
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"RUC: {proveedor.ruc}")   
        y -= 15
        pdf.drawString(50, y, f"NOMBRE: {proveedor.nombre}")
        y -= 15
        pdf.drawString(50, y, f"Contacto: {proveedor.telefono or '-'}")
        y -= 15
        pdf.drawString(50, y, f"Email: {proveedor.correo or '-'}")
        y -= 15
        pdf.drawString(50, y, f"Dirección: {proveedor.direccion or '-'}")
        y -=30

    pdf.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    response.write(pdf_data)
    return response

# Función para generar reporte de clientes
def reporte_clientes(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_clientes.pdf"'  # Mostrar en navegador

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    ancho, height = letter

    # Fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(35, height - 40, f"FECHA DE REPORTE: {fecha_actual}")

    #INFORMACION DE LA EMPRESA
    pdf.drawString(35, height - 55, "DIRECCIONES : Jr moquegua 734   JUNIN-HUANCAYO-HUANCAYO")
    pdf.drawString(35, height - 70, "TELEFONO : 965650117")
    pdf.drawString(35, height - 85, "RUC : 20487151921")
    
    # Logo de la empresa
    logo_path = os.path.join('Programa/static/img', 'logo_logix.png')
    try:
        pdf.drawImage(logo_path, ancho - 2.5 * inch, height - 1.5 * inch, width=2 * inch, height=0.7 * inch, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar el logo: {e}")

    # Encabezado del reporte
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 120, "Reporte de Clientes")
    pdf.setFont("Helvetica", 12)

    y = height - 170  # Espaciado inicial

    # Iterar sobre los clientes
    for cliente in Cliente.objects.all():
        if y < 100:  # Crear nueva página si no hay espacio
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 12)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"{cliente.nombre} {cliente.apellido or ''}")
        y -= 20
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"DNI: {cliente.dni}")
        y -= 15
        pdf.drawString(50, y, f"Teléfono: {cliente.telefono or '-'}                 Email: {cliente.correo or '-'}")
        y -= 30

    pdf.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    response.write(pdf_data)
    return response

# Función para generar reporte de usuarios
def reporte_usuarios(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_usuarios.pdf"'  # Mostrar en navegador

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    ancho, height = letter

    # Fecha actual
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(35, height - 40, f"FECHA DE REPORTE : {fecha_actual}")

    #INFORMACION DE LA EMPRESA
    pdf.drawString(35, height - 55, "DIRECCIONES : Jr moquegua 734   JUNIN-HUANCAYO-HUANCAYO")
    pdf.drawString(35, height - 70, "TELEFONO : 965650117")
    pdf.drawString(35, height - 85, "RUC : 20487151921")
    
    # Logo de la empresa
    logo_path = os.path.join('Programa/static/img', 'logo_logix.png')
    try:
        pdf.drawImage(logo_path, ancho - 2.5 * inch, height - 1.5 * inch, width=2 * inch, height=0.7 * inch, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar el logo: {e}")

    # Encabezado del reporte
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, height - 130, "Reporte de Usuarios")
    pdf.setFont("Helvetica", 12)

    y = height - 170  # Espaciado inicial

    # Usuarios administradores
    for usuario in Usuario.objects.filter(is_admin=True):
        if y < 100:  # Crear nueva página si no hay espacio
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 12)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"Administrador: {usuario.nombre} {usuario.apellidos}")
        y -= 20
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"DNI: {usuario.dni}")
        y -= 15
        pdf.drawString(50, y, f"Teléfono: {usuario.telefono}                Email: {usuario.correo}                 Edad: {usuario.edad} años")
        y -= 30

    # Usuarios vendedores
    for usuario in Usuario.objects.filter(is_admin=False):
        if y < 100:  # Crear nueva página si no hay espacio
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 12)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"Vendedor: {usuario.nombre} {usuario.apellidos}")
        y -= 20
        pdf.setFont("Helvetica", 12)
        pdf.drawString(50, y, f"DNI: {usuario.dni}")
        y -= 15
        pdf.drawString(50, y, f"Teléfono: {usuario.telefono}                Email: {usuario.correo}                 Edad: {usuario.edad} años")
        y -= 30

    pdf.save()
    pdf_data = buffer.getvalue()
    buffer.close()
    response.write(pdf_data)
    return response

# Enviar el PDF por correo
class EnviarReportePDF(APIView):
    def post(self, request):
        try:
            archivo_pdf = request.FILES.get('archivo_pdf')
            if not archivo_pdf:
                return Response({'message': 'No se envió un archivo PDF. Por favor, adjunta un archivo.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if archivo_pdf.content_type != 'application/pdf':
                return Response({'message': f'El archivo enviado no es válido ({archivo_pdf.content_type}). Solo se permiten archivos PDF.'}, status=status.HTTP_400_BAD_REQUEST)

            if archivo_pdf.size == 0:
                return Response({'message': 'El archivo está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

            self.enviar_correo(archivo_pdf)

            ventas = Venta.objects.all().order_by('-fecha_venta')[:10]
            return Response({'message': 'Reporte enviado satisfactoriamente.', 'ventas': list(ventas.values())}, status=status.HTTP_200_OK)
        
        except ValidationError as ve:
            return Response({'message': f'Error de validación: {str(ve)}'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': f'Error inesperado al enviar el reporte: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def enviar_correo(self, archivo_pdf):
        try:
            to_email = "jackblas29jack@gmail.com"
            subject = "Reporte de Silicon"
            message = "Se adjunta el reporte solicitado."

            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[to_email],
            )
            email.attach(archivo_pdf.name, archivo_pdf.read(), archivo_pdf.content_type)
            email.send()
        except BadHeaderError:
            raise ValidationError("Encabezado inválido en el correo.")
        except Exception as e:
            raise ValidationError(f"Error al enviar el correo: {str(e)}")
