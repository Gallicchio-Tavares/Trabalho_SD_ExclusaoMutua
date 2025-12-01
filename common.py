# common.py, pra funções utilitarias e formatação de msgs fixas

F = 32  # tamanho fixo das mensagens em bytes
SEP = "|"

# IDs de mensagens
MSG_REQUEST = "1"
MSG_GRANT   = "2"
MSG_RELEASE = "3"


def build_message(msg_id: str, pid: int) -> bytes:
    base = f"{msg_id}{SEP}{pid}{SEP}"
    padded = base.ljust(F, "0")
    return padded.encode()


def parse_message(data: bytes):
    s = data.decode().rstrip("0")
    parts = s.split(SEP)
    return parts[0], int(parts[1])
