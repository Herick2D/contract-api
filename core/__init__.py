__version__ = "1.0.0"


from .service import ProcessingService

from .models import Inquilino, Proprietario, Imovel, Contrato

__all__ = ["ProcessingService", "Inquilino", "Proprietario", "Imovel", "Contrato"]
