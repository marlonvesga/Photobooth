import cv2
import time
import os
import numpy as np
import win32print
import win32ui
import win32con
from PIL import Image, ImageTk, ImageWin
import tkinter as tk
from tkinter import messagebox

# Variables globales
cuenta_regresiva_activa = False
tiempo_captura = 4
fotos_restantes = 4
inicio_cuenta = None
tiempo_sonrie = 1

# Configuración de la cámara web/ Here you choose which camera use from 0 to 6 , 0 is predeterminated
cap = cv2.VideoCapture(0)

# Verificar si la carpeta "fotos" existe / Folder to save  the photos "fotos"
if not os.path.exists('fotos'):
    os.makedirs('fotos')

# Cargar los marcos / here loads the frames for the photos
marcos = [
    cv2.imread('marco/marco1.png', cv2.IMREAD_UNCHANGED),
    cv2.imread('marco/marco2.png', cv2.IMREAD_UNCHANGED),
    cv2.imread('marco/marco3.png', cv2.IMREAD_UNCHANGED)
]

# Listas para almacenar las fotos/ photos with and without frames
fotos_con_marco = []
fotos_sin_marco = []

def imprimir_imagen(ruta_imagen):
    try:
        imagen = Image.open(ruta_imagen)
        impresora = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(impresora)
        printer_info = win32print.GetPrinter(hprinter, 2)
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(impresora)
        printable_area = hdc.GetDeviceCaps(win32con.HORZRES), hdc.GetDeviceCaps(win32con.VERTRES)
        printer_size = hdc.GetDeviceCaps(win32con.PHYSICALWIDTH), hdc.GetDeviceCaps(win32con.PHYSICALHEIGHT)
        aspect_ratio = imagen.size[0] / imagen.size[1]

        if aspect_ratio > 1:
            new_width = printable_area[0]
            new_height = int(new_width / aspect_ratio)
        else:
            new_height = printable_area[1]
            new_width = int(new_height * aspect_ratio)
        
        hdc.StartDoc(ruta_imagen)
        hdc.StartPage()
        
        dib = ImageWin.Dib(imagen)
        scaled_width = int((printer_size[0] * new_width) / printable_area[0])
        scaled_height = int((printer_size[1] * new_height) / printable_area[1])
        x = int((printer_size[0] - scaled_width) / 2)
        y = int((printer_size[1] - scaled_height) / 2)
        
        dib.draw(hdc.GetHandleOutput(), (x, y, x + scaled_width, y + scaled_height))
        
        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()
        win32print.ClosePrinter(hprinter)
        
        return True, "Impresión exitosa"
        
    except Exception as e:
        return False, f"Error al imprimir: {str(e)}"

def superponer_marco(imagen, foto_numero):
    marco = marcos[foto_numero % len(marcos)]
    marco_redimensionado = cv2.resize(marco, (imagen.shape[1], imagen.shape[0]))
    marco_rgb = marco_redimensionado[:, :, :3]
    marco_alpha = marco_redimensionado[:, :, 3] / 255.0

    for c in range(0, 3):
        imagen[:, :, c] = (1. - marco_alpha) * imagen[:, :, c] + marco_alpha * marco_rgb[:, :, c]
    return imagen

def iniciar_toma():
    global cuenta_regresiva_activa, inicio_cuenta, fotos_restantes
    if not cuenta_regresiva_activa:
        cuenta_regresiva_activa = True
        inicio_cuenta = time.time()

def cerrar_aplicacion():
    cap.release()
    cv2.destroyAllWindows()
    root.destroy()

def actualizar_frame():
    global cuenta_regresiva_activa, inicio_cuenta, fotos_restantes

    ret, frame = cap.read()
    if not ret:
        return

    frame_con_marco = superponer_marco(frame.copy(), 3 - fotos_restantes)

    if cuenta_regresiva_activa:
        tiempo_restante = int(tiempo_captura - (time.time() - inicio_cuenta))
        
        if tiempo_restante > 0:
            texto = str(tiempo_restante)
            (text_width, text_height), baseline = cv2.getTextSize(texto, cv2.FONT_HERSHEY_SIMPLEX, 4, 8)
            x = (frame_con_marco.shape[1] - text_width) // 2
            y = (frame_con_marco.shape[0] + text_height) // 2
            cv2.putText(frame_con_marco, texto, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 8)
        elif tiempo_restante <= 0 and (time.time() - inicio_cuenta) < (tiempo_captura + tiempo_sonrie):
            texto = "!Sonrie!"
            fuente = cv2.FONT_HERSHEY_SIMPLEX
            (text_width, text_height), baseline = cv2.getTextSize(texto, fuente, 4, 8)
            x = (frame_con_marco.shape[1] - text_width) // 2
            y = (frame_con_marco.shape[0] + text_height) // 2
            cv2.putText(frame_con_marco, texto, (x, y), fuente, 4, (255, 255, 255), 8)
        else:
            nombre_foto_sin_marco = f"fotos/foto_sin_marco_{3 - fotos_restantes}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(nombre_foto_sin_marco, frame)
            fotos_sin_marco.append(frame)

            frame_con_marco_guardar = superponer_marco(frame.copy(), 3 - fotos_restantes)
            nombre_foto_con_marco = f"fotos/foto_con_marco_{3 - fotos_restantes}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(nombre_foto_con_marco, frame_con_marco_guardar)
            fotos_con_marco.append(frame_con_marco_guardar)

            fotos_restantes -= 1

            if fotos_restantes > 0:
                inicio_cuenta = time.time()
            else:
                cuenta_regresiva_activa = False
                fotos_restantes = 3

                imagen_combinada = np.vstack(fotos_con_marco)
                nombre_combinada = f"fotos/imagen_combinada_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(nombre_combinada, imagen_combinada)
                
                exito, mensaje = imprimir_imagen(nombre_combinada)
                if exito:
                    print("Imagen combinada impresa exitosamente")
                else:
                    print(f"Error al imprimir la imagen combinada: {mensaje}")

                fotos_con_marco.clear()
                fotos_sin_marco.clear()

    # Mostrar el video en la interfaz de tkinter
    frame_rgb = cv2.cvtColor(frame_con_marco, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame_rgb)
    imgtk = ImageTk.PhotoImage(image=img)
    label_video.imgtk = imgtk
    label_video.configure(image=imgtk)
    root.after(10, actualizar_frame)

# Interfaz de usuario con tkinter
root = tk.Tk()
root.title("PhotoBooth Free")
root.geometry("1024x768")

label_video = tk.Label(root)
label_video.pack()

boton_iniciar = tk.Button(root, text="Iniciar/ Start", command=iniciar_toma, font=("Arial", 12), bg="green", fg="white")
boton_iniciar.pack(pady=10)

boton_cerrar = tk.Button(root, text="Cerrar/Close", command=cerrar_aplicacion, font=("Arial", 12), bg="red", fg="white")
boton_cerrar.pack(pady=10)

# Iniciar actualización del frame
actualizar_frame()

root.mainloop()
