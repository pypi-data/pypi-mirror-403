from pydantic import BaseModel
from typing import Union, Optional
from pathlib import Path
from io import BytesIO
from stackraise.model.file import File

class ImageData(BaseModel):
    """Modelo para representar imágenes en el contexto de plantillas PPTX"""
    
    # Datos de la imagen
    data: Union[bytes, str, Path]  # bytes, ruta como string, o Path object
    
    # Metadatos opcionales
    width: Optional[float] = None  # Ancho en pulgadas
    height: Optional[float] = None  # Alto en pulgadas
    
    # Para mantener aspect ratio
    max_width: Optional[float] = None
    max_height: Optional[float] = None
    
    @classmethod
    def from_bytes(cls, data: bytes, width: Optional[float] = None, height: Optional[float] = None):
        """Crear ImageData desde bytes"""
        return cls(data=data, width=width, height=height)
    
    @classmethod
    def from_path(cls, path: Union[str, Path], width: Optional[float] = None, height: Optional[float] = None):
        """Crear ImageData desde ruta de archivo"""
        return cls(data=Path(path), width=width, height=height)
    
    @classmethod
    def from_url(cls, url: str, width: Optional[float] = None, height: Optional[float] = None):
        """Crear ImageData desde URL (requiere descarga previa)"""
        # TODO: Implementar descarga de imagen desde URL
        return cls(data=url, width=width, height=height)
    
    @classmethod
    async def from_file_ref(cls, file_ref: File.Ref):
        file: File = await file_ref.fetch()
        content = await file.content()
        return cls.from_bytes(content)

    def get_bytes(self) -> bytes:
        """Obtener los bytes de la imagen"""
        if isinstance(self.data, bytes):
            return self.data
        elif isinstance(self.data, (str, Path)):
            with open(self.data, 'rb') as f:
                return f.read()
        else:
            raise ValueError(f"Tipo de data no soportado: {type(self.data)}")