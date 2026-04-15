# Standard Library & Dependancies
import json, tempfile, weakref
from typing import Optional
from urllib.parse import urljoin
# external libs
import requests
import gnupg

EXPECTED_NOTE_TYPES: dict[str, type] = {
    "title": str,
    "content": str,
    "pinned": bool,
    "favorite": bool,
    "readonly": bool,
    "archived": bool,
    "notebookIds": list,
    "tagIds": list,
    "source": str,
}

def validate_payload(payload: dict[str, object]) -> None:
    for key, expected_type in EXPECTED_NOTE_TYPES.items():
        if key not in payload:
            raise KeyError(f"Missing key: {key}")

        value = payload[key]
        if not isinstance(value, expected_type):
            got = type(value).__name__
            want = expected_type.__name__
            raise TypeError(f"{key} must be {want}, got {got}")

class Notesnook_Inbox():
    def __init__(self, apikey: str, pubkey: Optional[str] = None, server: str="https://api.notesnook.com/inbox/"):
        self.server = server
        self.apikey = apikey
        self._temp_dir = tempfile.TemporaryDirectory()
        self._finalizer = weakref.finalize(self, self._temp_dir.cleanup)
        self._gpg = gnupg.GPG(gnupghome=self._temp_dir.name)
        if pubkey is None:
            response = requests.get(urljoin(self.server, "public-encryption-key"), headers={"Authorization": self.apikey})
            pubkey = response.json()["key"]
        imported_keys = self._gpg.import_keys(key_data=pubkey)
        if not imported_keys.fingerprints:
            raise ValueError("Failed to import public key.")
        self._recipient = imported_keys.fingerprints[0]
    
    def create_note(self, title: str, content: str, source: str, pinned:bool= False, favorite:bool= False, readonly:bool= False, archived:bool= False, notebookIds: list[str]=None, tagIds: list[str]=None):
        if notebookIds is None:
            notebookIds = []
        if tagIds is None:
            tagIds = []
        if len(title) < 1:
            raise KeyError("Title must be at least 1 character long.")
        if len(content) < 1:
            raise KeyError("Content must be at least 1 character long.")
        if len(source) < 1:
            raise KeyError("You must include source metadata that describes where this note was sent from.")
        validate_payload(
            {
                "title": title,
                "content": content,
                "pinned": pinned,
                "favorite": favorite,
                "readonly": readonly,
                "archived": archived,
                "notebookIds": notebookIds,
                "tagIds": tagIds,
                "source": source,
            }
        )

        for key, thing in (("notebookIds", notebookIds), ("tagIds", tagIds)):
            if not all(isinstance(item, str) for item in thing):
                raise TypeError(f"{key} must be list[str]")

        note_dict = {
            "title": title,
            "pinned": pinned,
            "favorite": favorite,
            "readonly": readonly,
            "archived": archived,
            "notebookIds": notebookIds,
            "tagIds": tagIds,
            "source": source,
            "type": "note",
            "content": {
                "type": "html",
                "data": content
            },
            "version": 1
        }

        note_str = json.dumps(note_dict).encode("UTF-8")

        encrypted_message = self._gpg.encrypt(
            note_str,
            self._recipient,
            always_trust=True,
            armor=True
        )
        if encrypted_message.ok:
            ciphertext = str(encrypted_message)
            if len(ciphertext) > (1000*1000*10): # 10 megabytes
                raise ValueError("Note ciphertext is too long to publish")
            
            note_message = {
                "v": 1,
                "cipher": ciphertext,
                "alg": "pgp-aes256"
            }
            
            post_request = requests.request("POST", urljoin(self.server, "items"), headers={"Content-Type": "application/json", "Authorization": self.apikey}, data=json.dumps(note_message), timeout=10)
            post_request.raise_for_status()
        else:
            raise RuntimeError(f"Failed to encrypt message.\nStatus: {encrypted_message.status}\n{encrypted_message.stderr}")
        return
        

            

if __name__ == "__main__":
    jsonconfig = open("config.json", "r").read()
    jsonconfig = json.loads(jsonconfig)
    test = Notesnook_Inbox(apikey=jsonconfig["apikey"])
    test.create_note("test", "<p>Hello!</p>", "Testing nn_inbox_py script")
