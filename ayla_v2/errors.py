class AppError(Exception):
    """Erro esperado, com mensagem adequada para exibição ao usuário."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)
