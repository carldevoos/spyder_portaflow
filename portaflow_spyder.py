#!/usr/bin/env python
# coding: utf-8

import requests
from datetime import datetime, timedelta
from requests import Request, Session
from bs4 import BeautifulSoup

class PortaflowSpyder:
    
    def __init__(self, day):
        """Variables de la clase"""
        
        self.url = None
        self.url_base = "http://localhost:8001"
        self.username = ''
        self.password = ''
        self.session = Session() #Se crea una session, esta guarda las cookies y los header, los usara automaticamente
        self.response = None
        self.date = datetime.today() - timedelta(days=day)
    
    
    def make_url(self, url):
        """Completa la url"""
        
        self.url = self.url_base + url
        
        
    def make_payload(self, payload, parser):
        """El ViewState es necesario para hacer cada Post(Similar al token). Se encuentra oculto en el formulario o en los response"""
        
        soup = BeautifulSoup(self.response.content, 'html.parser')
        
        if parser == 'html':
            view_state = soup.find('input', {"name":"javax.faces.ViewState"})['value']
        elif parser == 'file':
            view_state = soup.find_all(text=True)[3]
        else:
            view_state = soup.find_all(text=True)[2]
        
        payload['javax.faces.ViewState'] = view_state
        
        return payload
    
    
    def redirect_URL(self):
        """Redirige a la URL que se encuentra en el response XML."""
        
        soup = BeautifulSoup(self.response.content,'lxml')
        url = soup.find_all('redirect')[0]['url']
        
        self.make_url(url)
        
        self.response = self.session.get(self.url)
        
    
    def login(self):
        """Realiza el login en la web."""
        
        payload_login = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'formLogin:loginButton',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'formLogin formLogin:messagesLogin',
            'formLogin:loginButton': 'formLogin:loginButton',
            'formLogin': ' formLogin',
            'formLogin:user': self.username,
            'formLogin:password': self.password,
            'javax.faces.ViewState': None
        }
        
        self.make_url('/Portaflow/faces/login.jsf')
        
        self.response = self.session.get(self.url)
        
        self.response = self.session.post(self.url, data = self.make_payload(payload_login, 'html'))
        
        self.redirect_URL()
        
    
    def daily_files(self):
        """Ingresa a las opciones para descargar los archivos"""
        
        payload_daily_files = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'menuform:j_idt16',
            'javax.faces.partial.execute': '@all',
            'menuform:j_idt16': 'menuform:j_idt16',
            'menuform:j_idt16_menuid': '2_0',
            'menuform': 'menuform',
            'javax.faces.ViewState': None
        }
        
        self.make_url('/Portaflow/templates/option.jsf')
        
        self.response = self.session.post(self.url, data = self.make_payload(payload_daily_files, 'html'))
        
        self.redirect_URL()
        
        self.set_date()
                

    def set_date(self):
        """Cambia la fecha de descarga del archivo, esto evita errores del cambio de mes o año."""
        
        payload_date = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'formMeses:buttonSearch',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'panelFicherosDiarios+panelFicherosTotales+formMeses:messages',
            'formMeses:buttonSearch': 'formMeses:buttonSearch',
            'formMeses': 'formMeses',
            'formMeses:monthList_focus': '',
            'formMeses:monthList_input': None,
            'formMeses:yearList_focus': '',
            'formMeses:yearList_input': None,
            'javax.faces.ViewState': None
        }
        
        months = {
            '01': 'enero',
            '02': 'febrero',
            '03': 'marzo',
            '04': 'abril',
            '05': 'mayo',
            '06': 'junio',
            '07': 'julio',
            '08': 'agosto',
            '09': 'septiembre',
            '10': 'octubre',
            '11': 'noviembre',
            '12': 'diciembre'
        }
        
        month = months[self.date.strftime('%m')]
        year = self.date.strftime('%Y')
        
        payload_date['formMeses:monthList_input'] = month
        payload_date['formMeses:yearList_input']  = year
        
        self.make_url('/Portaflow/templates/option.jsf')
        
        self.response = self.session.post(self.url, data = self.make_payload(payload_date, 'html'))
        
    
    def download_file(self):
        """Descargamos el archivo, primero se hace el post de seleccion del file y luego el post para descargar."""
        
        filename = f"NumeracionesPortadas_{self.date.strftime('%Y%m%d')}.gz";
        
        payload_file = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'panelFicherosTotales:formConsolidacion:idConsolidacion',
            'javax.faces.partial.execute': 'panelFicherosTotales:formConsolidacion:idConsolidacion',
            'javax.faces.partial.render': 'panelFicherosTotales:formConsolidacion',
            'javax.faces.behavior.event': 'change',
            'javax.faces.partial.event': 'change',
            'panelFicherosTotales:formConsolidacion': 'panelFicherosTotales:formConsolidacion',
            'panelFicherosTotales:formConsolidacion:idConsolidacion_input': filename,
            'javax.faces.ViewState': None
        }
        
        self.response = self.session.post(self.url, data = self.make_payload(payload_file, 'xml'))
        
        payload_download = {
            'panelFicherosTotales:formConsolidacion': 'panelFicherosTotales:formConsolidacion',
            'panelFicherosTotales:formConsolidacion:idConsolidacion_input': filename,
            'javax.faces.ViewState': None
        }
        
        # Es necesario obtener el id, ya que se usa en el post
        soup = BeautifulSoup(self.response.content,'lxml')
        payload_download[soup.find('button')['id']] = ''
        
        print(filename)
        
        local_filename = f'/tmp/{filename}'
        
        # Se añade stream para no perder la conexion
        # No se tiene el peso del archivo, por lo que no se puede hacer una barra de progreso
        with self.session.post(self.url, data = self.make_payload(payload_download, 'file'), stream = True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=102400): 
                    f.write(chunk)

if __name__ == '__main__':
    # Inciamos el objeto, indicamos numero de dias atras a cargar
    pf = PortaflowSpyder(1)
    pf.login()
    pf.daily_files()
    pf.download_file()