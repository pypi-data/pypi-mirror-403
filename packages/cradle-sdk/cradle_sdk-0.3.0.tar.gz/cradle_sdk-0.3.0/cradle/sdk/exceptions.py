class ClientError(Exception):
    def __init__(self, status_code: int, message: str, errors: list[str]):
        self.status_code = status_code
        self.message = message

        message = f"API Error {status_code}: {message}"
        if len(errors) > 0:
            error_list = "\n".join(f"\t{error}" for error in errors)
            message = f"{message}\n{error_list}"

        super().__init__(message)
