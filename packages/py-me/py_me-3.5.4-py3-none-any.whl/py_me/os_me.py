import os
from datetime import datetime
import io
from rich.traceback import install, Console
import json
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
import locale
import inspect
import re
from typing import Dict, Union, Optional
from pathlib import Path

class NoReturn:
  pass

@dataclass
class Details:
    log_file: str = "log.txt"
    timeline_file: str = "TIMELINE_os_me.json"

    encoding: str = "utf-8"

    language: str = "en"

    enable_logging: bool = True
    enable_rich_traceback: bool = True
    auto_snapshot_on_edit: bool = True
    avoid_duplicate_snapshots: bool = True

    timestamp_format: str = "%d/%m/%Y %H:%M:%S"

    custom_logger: Optional[Callable[[str], None]] = None

    silent_FileHunter: bool = False

    _messages: dict = field(default_factory=lambda: {
        "en": {
            "start_flow": "[--__START OF FLOW__--]",
            "edit": "[EDIT] {}° flow event: {} was edited",
            "add": "[ADD] {}° flow event: content added to {}",
            "create": "[CREATE] {}° flow event: {} was created",
            "undo": "[UNDO] {}° flow event: {} restored to version {}",
            "error": "[ERROR] {}° flow event: {}",
            "file_not_found": "{} not found",
            "file_exists": "{} already exists",
            "undo_err": "[ERROR] {numero}° flow event: command undo invalid ({content})",
            "lost version": "version {} not found for {}",
            "add_err": "error while trying to ass {} error type: {}",
            "exec": "[EXEC] {}° flow event: {} executed successfully!",
            "exec_error": "error executing {} error type: {}",
            "error_sequence": "[ERROR_SEQUNECE] {}° flow event: error encountered during execution: {}",
            "error_list": "the specific list is an empty list",
            "error_not_list": "{} is not a list"
        },
        "pt": {
            "start_flow": "[--__INICIO DE FLUXO__--]",
            "edit": "[EDIT] {}° evento de fluxo: {} foi editado",
            "add": "[ADD] {}° evento de fluxo: conteúdo adicionado a {}",
            "create": "[CREATE] {}° evento de fluxo: {} foi criado",
            "undo": "[UNDO] {}° evento de fluxo: {} restaurado para versão {}",
            "error": "[ERROR] {}° evento de fluxo: {}",
            "file_not_found": "{} não existe",
            "file_exists": "{} já existe",
            "undo_err": "[ERROR] {}° evento de fluxo: comando undo inválido ({})",
            "lost version": "versão {} não encontrada para {}",
            "add_err": "erro ao tentar adicionar {} tipo de erro: {}",
            "exec": "[EXEC] {}° evento de fluxo: {} executado com exito!",
            "exec_error": "erro na execução de {} tipo de erro: {}",
            "error_sequence": "[ERROR_SEQUENCE] Evento de fluxo {}: erro encontrado durante a execução: {}",
            "error_list": "a lista especificada é uma lista vazia",
            "error_not_list": "{} não é uma lista"
        }
    })

    def helper(self, atribute: str = "...") -> str:
      if atribute == "log_file":
         if self.language == "en":
            return "Defines the file where the logging will be done."
         elif self.language == "pt":
            return "Define o arquivo onde o registro de log será feito."
      elif atribute == "timeline_file":
        if self.language == "en":
            return "Specifies the file used to store the timeline of file edits."
        elif self.language == "pt":
            return "Especifica o arquivo usado para armazenar a linha do tempo das edições de arquivos."
      elif atribute == "encoding":
        if self.language == "en":
            return "Sets the character encoding for file operations."
        elif self.language == "pt":
            return "Define a codificação de caracteres para operações de arquivo."
      elif atribute == "language":
        if self.language == "en":
            return "Sets the language for messages and logs."
        elif self.language == "pt":
            return "Define o idioma para mensagens e logs."
      elif atribute == "enable_logging":
        if self.language == "en":
            return "Enables or disables logging of operations."
        elif self.language == "pt":
            return "Habilita ou desabilita o registro de operações."
      elif atribute == "enable_rich_traceback":
        if self.language == "en":
            return "Enables or disables rich tracebacks for error handling."
        elif self.language == "pt":
            return "Habilita ou desabilita rastreamentos ricos para tratamento de erros."
      elif atribute == "auto_snapshot_on_edit":
        if self.language == "en":
            return "Automatically creates snapshots of files before edits."
        elif self.language == "pt":
            return "Cria automaticamente snapshots dos arquivos antes das edições."
      elif atribute == "avoid_duplicate_snapshots":
        if self.language == "en":
            return "Prevents creating duplicate snapshots with identical content."
        elif self.language == "pt":
            return "Evita a criação de snapshots duplicados com conteúdo idêntico."
      elif atribute == "timestamp_format":
        if self.language == "en":
            return "Specifies the format for timestamps in logs."
        elif self.language == "pt":
            return "Especifica o formato para timestamps nos logs."
      elif atribute == "silent_FileHunter":
        if self.language == "en":
          return "Silences print outputs and os_me_error from all FileHunter methods."
        elif self.language == "pt":
          return "Silencia as saídas de print e os_me_error de todos os métodos FileHunter"
      else:
        if self.language == "en":
          all_for_help = "log_file: Defines the file where the logging will be done.\n" \
                         "timeline_file: Specifies the file used to store the timeline of file edits.\n" \
                         "encoding: Sets the character encoding for file operations.\n" \
                         "language: Sets the language for messages and logs.\n" \
                         "enable_logging: Enables or disables logging of operations.\n" \
                         "enable_rich_traceback: Enables or disables rich tracebacks for error handling.\n" \
                         "auto_snapshot_on_edit: Automatically creates snapshots of files before edits.\n" \
                         "avoid_duplicate_snapshots: Prevents creating duplicate snapshots with identical content.\n" \
                         "timestamp_format: Specifies the format for timestamps in logs.\n" \
                         "silent_FileHunter: Silences print outputs and os_me_error from all FileHunter methods."
          return all_for_help
        elif self.language == "pt":
          all_for_help = "log_file: Define o arquivo onde o registro de log será feito.\n" \
                         "timeline_file: Especifica o arquivo usado para armazenar a linha do tempo das edições de arquivos.\n" \
                         "encoding: Define a codificação de caracteres para operações de arquivo.\n" \
                         "language: Define o idioma para mensagens e logs.\n" \
                         "enable_logging: Habilita ou desabilita o registro de operações.\n" \
                         "enable_rich_traceback: Habilita ou desabilita rastreamentos ricos para tratamento de erros.\n" \
                         "auto_snapshot_on_edit: Cria automaticamente snapshots dos arquivos antes das edições.\n" \
                         "avoid_duplicate_snapshots: Evita a criação de snapshots duplicados com conteúdo idêntico.\n" \
                         "timestamp_format: Especifica o formato para timestamps nos logs.\n" \
                         "silent_FileHunter: Silencia as saídas de print e os_me_error de todos os métodos FileHunter"
          return all_for_help
    def get_message(self, key: str, *args, **fmt) -> str:
      lang_dict = self._messages.get(self.language, self._messages["en"])
      msg = lang_dict.get(key, key)  # fallback
      if args or fmt:
        # primeira tentativa: usar args posicionais e kwargs nominais
        try:
          return msg.format(*args, **fmt)
        except Exception:
          # se falhar, tente usar apenas args posicionais
          try:
            return msg.format(*args)
          except Exception:
            # se ainda falhar e houver kwargs, tente usar os valores dos kwargs
            if fmt:
              try:
                return msg.format(*fmt.values())
              except Exception:
                try:
                  return msg.format(**fmt)
                except Exception:
                  return msg
            return msg
      return msg

class OsMeError(Exception):
  def __init__(self, exception):
    super().__init__(exception)
    self.exception = exception

class utilidades:
    def __init__(self, details: Details):
        self.details = details
    
    def registrar_log(self, mensagem: str) -> NoReturn:
        if not self.details.enable_logging:
            return
        if self.details.custom_logger:
            self.details.custom_logger(mensagem)
            return
        
        with open(self.details.log_file, "a", encoding=self.details.encoding) as log:
            timestamp = datetime.now().strftime(self.details.timestamp_format)
            log.write(f"[{timestamp}] {mensagem}\n")

class file_class:
  def __init__(self, details: Details = None):
    self.details = details or Details()  # default config
    self.utilidades = utilidades(self.details)
    self.ultilidades = self.utilidades
    self.numero = 1
    self.inicio_de_fluxo = True
    self.lista_de_erros = []
    self.numero_versao = 1
    if self.details.enable_rich_traceback:
      install()

  def replace(self, path: str, content: str) -> NoReturn:
    """
    Replaces all the content of the specified file with new content, or undoes to a previous version by specifying "undo X", where "X" is the file version number.

    Args:
        path(str): The path to the file that will be altered.
        content(str): The new content to be placed, or "undo X" for restoration.

    Behavior:
        - Creates a snapshot of the current content before changes if auto_snapshot_on_edit is enabled.
        - Replaces the file content if not an undo command.
        - Restores from the timeline if "undo X" is specified.
        - Logs the operation and handles errors like file not found or invalid undo.

    Example:
        >>> from py_me import os_me
        >>> os_me.file.replace("my\\file.txt", "hello")
        >>> os_me.file.replace("my\\file.txt", "undo 1")  # Restores version 1

    Returns:
        None
    """
    if self.inicio_de_fluxo:
        if self.details.enable_logging:
          self.utilidades.registrar_log(
            self.details.get_message("start_flow")
          )
          self.inicio_de_fluxo = False

    if not os.path.exists(path):
        try:
            raise OsMeError(
               self.details.get_message("file_not_found", caminho = path)
            )
        except OsMeError as a:
            if self.details.enable_rich_traceback:
              console = Console()
              console.print_exception()
            if self.details.enable_logging:
              self.utilidades.registrar_log(
                self.details.get_message("error", number= self.numero, message= a)
              )
              self.numero += 1
              return

    # Ler conteúdo atual
    with open(path, "r", encoding="utf-8") as filer_r:
        conteudo_atual = filer_r.read()

    # Criar snapshot
    if self.details.auto_snapshot_on_edit:
      snapshot = {
        "versao": self.numero_versao,
        "timestamp": datetime.now().isoformat(),
        "conteudo": conteudo_atual
      }

      # Atualizar timeline
      if os.path.exists(self.details.timeline_file) and os.path.getsize(self.details.timeline_file) > 0:
          try:
              with open(self.details.timeline_file, "r", encoding="utf-8") as f:
                  data = json.load(f)
          except json.JSONDecodeError:
              data = {}
      else:
          data = {}

      if path not in data:
          data[path] = []

      # Evitar duplicação de versão e conteúdo
      versoes_existentes = [s["versao"] for s in data[path]]
      conteudos_existentes = [s["conteudo"] for s in data[path]]

      if snapshot["conteudo"] in conteudos_existentes:
        # já existe esse conteúdo, não precisa salvar de novo
        pass
      else:
        # garantir que o número da versão seja único
        while snapshot["versao"] in versoes_existentes:
          self.numero_versao += 1
          snapshot["versao"] = self.numero_versao

        data[path].append(snapshot)


      with open(self.details.timeline_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

      self.numero_versao += 1

      # Escrever novo conteúdo ou desfazer
      with open(path, "w", encoding="utf-8") as filer:
          if content.startswith("undo"):
              try:
                  versao_pedida = int(content.split()[1])
              except (IndexError, ValueError):
                  if self.details.enable_logging:
                    self.ultilidades.registrar_log(
                      self.details.get_message("undo_err", numero = self.numero, content = content)
                    )
                  return

              if path in data:
                for snapshot in data[path]:
                    if snapshot["versao"] == versao_pedida:
                        filer.write(snapshot["conteudo"])
                        if self.details.enable_logging:
                          self.ultilidades.registrar_log(
                            self.details.get_message("undo", number = self.numero, path = path, version = versao_pedida)
                          )
                        self.numero += 1
                        return
              try:
                 raise OsMeError(self.details.get_message("file_not_found", caminho = path))
              except OsMeError:
                if self.details.enable_logging:
                  self.ultilidades.registrar_log(
                    self.details.get_message("error", number = self.numero, conteudo = self.details.get_message("file_not_found", caminho = path))
                  )
          else:
            filer.write(content)
            if self.details.enable_logging:
              self.ultilidades.registrar_log(
                self.details.get_message("edit", number = self.numero)
              )
            self.numero += 1

  def create(self, new_path: str, content: str = "") -> str:
    """
    Creates a new file at the specified path with optional initial content.

    Args:
        new_path(str): The path where the file will be created.
        content(str optional): Initial content to write; defaults to empty.

    Behavior:
        - Checks if the file already exists and raises an error if it does.
        - Creates the file and writes the content.
        - Logs the creation event if logging is enabled.

    Example:
        >>> from py_me import os_me
        >>> os_me.file.create("new_file.txt", "Initial text")
        'new_file.txt'

    Returns:
        str (the path of the created file)
    """
    if self.inicio_de_fluxo == True:
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("start_flow")
        )
        self.inicio_de_fluxo = False
    if not os.path.exists(new_path):
        with open(new_path, "x", encoding="utf-8") as filer:
          filer.write(content)
        if self.details.enable_logging:
          self.ultilidades.registrar_log(
              self.details.get_message("create", numero = self.numero)
          )
          self.numero += 1
          return new_path
    else:
          try:
            raise OsMeError(self.details.get_message("file_exists", ooo = new_path))
          except OsMeError as a:
            if self.details.enable_rich_traceback == True:
              console = Console()
              console.print_exception()
            if self.details.enable_logging:
              self.ultilidades.registrar_log(
                self.details.get_message("error", numero = self.numero, erro = self.details.get_message("file_exists", ooo = new_path))
              )
              self.numero += 1

  def add(self, path: str, content: str) -> NoReturn:
    """
    Appends new content to the end of an existing file.

    Args:
        path(str): The path to the file to append to.
        content(str): The content to add.

    Behavior:
        - Appends the content if the file exists.
        - Logs the addition event.
        - Handles errors like file not found.

    Example:
        >>> from py_me import os_me
        >>> os_me.file.add("my_file.txt", "Appended text")

    Returns:
        None
    """
    with open(path, "r", encoding="utf-8") as filer_r:
      conteudo_atual = filer_r.read()
    
    # Criar snapshot
    if self.details.auto_snapshot_on_edit:
      snapshot = {
        "versao": self.numero_versao,
        "timestamp": datetime.now().isoformat(),
        "conteudo": conteudo_atual
      }

      # Atualizar timeline
      if os.path.exists(self.details.timeline_file) and os.path.getsize(self.details.timeline_file) > 0:
          try:
              with open(self.details.timeline_file, "r", encoding="utf-8") as f:
                  data = json.load(f)
          except json.JSONDecodeError:
              data = {}
      else:
          data = {}

      if path not in data:
          data[path] = []

      # Evitar duplicação de versão e conteúdo
      versoes_existentes = [s["versao"] for s in data[path]]
      conteudos_existentes = [s["conteudo"] for s in data[path]]

      if snapshot["conteudo"] in conteudos_existentes:
        # já existe esse conteúdo, não precisa salvar de novo
        pass
      else:
        # garantir que o número da versão seja único
        while snapshot["versao"] in versoes_existentes:
          self.numero_versao += 1
          snapshot["versao"] = self.numero_versao

        data[path].append(snapshot)
      if not os.path.exists(path):
        try:
          raise OsMeError(self.details.get_message("file_not_found", caminho = path))
        except OsMeError:
          if self.details.enable_rich_traceback:
            console = Console()
            console.print_exception()
          if self.details.enable_logging:
            self.ultilidades.registrar_log(
              self.details.get_message("error", numero = self.numero, erro = self.details.get_message("add_err", verção = self.numero_versao, erro = self.details.get_message("file_not_found", caminho = path)))
            )
            self.numero += 1
      else:
        with open(self.details.timeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        self.numero_versao += 1
    if self.inicio_de_fluxo == True:
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("start_flow")
        )
        self.inicio_de_fluxo = False
    if os.path.exists(path):
      with open(path, "a", encoding="utf-8") as so:
        so.write(content)
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("add", numero = self.numero)
        )

  def execution_sequence(self, paths: list, ignore_error: bool = False, list_erros: bool = False) -> NoReturn:
    """
    Executes Python code from one or more files, with options to ignore errors or list them.

    Args:
        paths(list): Path(s) to the file(s) to execute.
        ignore_error(bool optional): If True, continues on errors; defaults to False.
        list_erros(bool optional): If True, returns a list of errors; defaults to False.

    Behavior:
        - Executes code in each file sequentially.
        - Captures output and errors.
        - Logs successful executions or errors.
        - Handles empty lists or non-list inputs with errors.

    Example:
        >>> from py_me import os_me
        >>> os_me.file.exec(["script1.py", "script2.py"])

    Returns:
        dict (execution results) or None
    """
    if self.inicio_de_fluxo == True:
      if self.details.enable_logging:
        self.ultilidades.registrar_log(
          self.details.get_message("start_flow")
        )
        self.inicio_de_fluxo = False
    if isinstance(paths, list):
      if paths:
        for filer in paths:
          if os.path.exists(filer):
            with open(filer, "r", encoding="utf-8") as exe:
              e = exe.read()
              try:
                exec(e, {})
                if self.details.enable_logging:
                  self.utilidades.registrar_log(
                    self.details.get_message("exec", numero = self.numero, exec = filer)
                  )
              except Exception as err:
                if ignore_error == True:
                   pass
                elif list_erros == True:
                   self.lista_de_erros.append(err)
                else:
                  if self.details.enable_logging:
                    self.utilidades.registrar_log(
                      self.details.get_message("exec_error", aaa = filer, tipo = err)
                    )
                  raise OsMeError(self.details.get_message("error", numero = self.numero,  error = err)) from err
              finally:
                if self.details.enable_logging:
                 self.numero +=1
          else:
            try:
              raise OsMeError(self.details.get_message("file_not_found", arquivo = filer))
            except OsMeError:
              if self.details.enable_rich_traceback:
                console = Console()
                console.print_exception()
              if self.details.enable_logging:
                self.utilidades.registrar_log(
                  self.details.get_message("error", numero = self.numero, erro = self.details.get_message("file_not_found", arquivo = filer))
                )
                self.numero +=1
        else:
          if list_erros:
            for erro in self.lista_de_erros:
              print(str(erro))
              if self.details.enable_logging:
                self.utilidades.registrar_log(
                  self.details.get_message("error_sequence", numero = self.numero, error = erro)
                )
                self.numero += 1
            self.lista_de_erros.clear()
      else:
        try:
          raise OsMeError(self.details.get_message("error_list"))
        except OsMeError:
          if self.details.enable_rich_traceback:
            console = Console()
            console.print_exception()
          if self.details.enable_logging:
            self.utilidades.registrar_log(
              self.details.get_message("error", numero = self.numero, erro = self.details.get_message("error_list"))
            )
            self.numero += 1
    else:
      try:
        raise OsMeError(self.details.get_message("error_not_list", lista = paths))
      except OsMeError:
        if self.details.enable_rich_traceback:
          console = Console()
          console.print_exception()
        if self.details.enable_logging:
          self.utilidades.registrar_log(
            self.details.get_message("error", numero = self.numero, erro = self.details.get_message("error_not_list", lista = paths))
          )

class path_class:
    def __init__(self, details: Details = None):
        self.FilerBust = None
        self.FilerBust_inverse = None
        self.details = details or Details() 
        install()

    def FileHunter(self, relative_path: str) -> str | None:
        """
    Searches for a file by ascending through parent directories from the current working directory.

    Args:
        relative_path(str): The relative path or filename to search for.

    Behavior:
        - Checks existence in current and parent directories recursively.
        - Stops at root directory.
        - Prints success/failure and raises error if not found.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.FileHunter("config.txt")
        '/path/to/config.txt'  # Or None if not found

    Returns:
        str (full path if found) or None
    """
        path = self.FilerBust or os.getcwd()
        a = os.path.join(path, relative_path)

        if os.path.exists(a):
          if not self.details.silent_FileHunter:
            print(f"{relative_path} exist: ✅")
          self.FilerBust = None
          return a
        else:
            pasta_pai = os.path.dirname(path)
            self.FilerBust = pasta_pai

            # condição de parada genérica: chegou na raiz
            if not pasta_pai == path:
                return self.FileHunter(relative_path)
            else:
                self.FilerBust = None
                if self.details.silent_FileHunter:
                  return None
                try:
                  raise OsMeError(f"{relative_path} exist: ❌")
                except OsMeError as a:
                  if self.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
                return None
            
    def FileHunter_inverse(self, relative_path: str, start: str = None) -> str | None:
      """
    Searches for a file or directory descending through subdirectories from a start path.

    Args:
        relative_path(str): The name or suffix to match.
        start(str optional): Starting directory; defaults to current working directory.

    Behavior:
        - Walks the directory tree and matches exact names or suffixes.
        - Prints success and returns first match.
        - Raises error if not found.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.FileHunter_inverse("config.txt", "/start/dir")
        '/start/dir/sub/config.txt'  # Or None

    Returns:
        str (full path if found) or None
    """
      if not start:
        start = os.getcwd()
      for root, dirs, files in os.walk(start):
        # procura por diretórios que batem exatamente ou pelo sufixo
        for d in dirs:
          candidate = os.path.join(root, d)
          if d == relative_path or candidate.endswith(relative_path):
            if not self.details.silent_FileHunter:
              print(f"{relative_path} exist: ✅")
            return candidate
        # procura por arquivos que batem exatamente ou pelo sufixo
        for f in files:
          candidate = os.path.join(root, f)
          if f == relative_path or candidate.endswith(relative_path):
            print(f"{relative_path} foi encontrada com sucesso em {root}")
            return candidate
      # não encontrado
      if self.details.silent_FileHunter:
        return None
      try:
        raise OsMeError(f"{relative_path} exist: ❌")
      except OsMeError:
        if self.details.enable_rich_traceback:
          console = Console()
          console.print_exception()
      return None

    def FileHunter_SUPER(self, relative_path: str) -> str | None:
      """
    Performs an advanced search starting from the user's home directory.

    Args:
        relative_path(str): The relative path or filename to search for.

    Behavior:
        - Combines FileHunter and FileHunter_inverse from home directory.
        - Returns the found path or None.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.FileHunter_SUPER("Documents/config.txt")
        '/home/user/Documents/config.txt'  # Or None

    Returns:
        str (full path if found) or None
    """
      a = self.FileHunter(relative_path)
      if a:
        return a
      else:
        user_home = os.path.expanduser("~")
        b = self.FileHunter_inverse(relative_path, user_home)
        return b

    def FileHunter_TrueOrFalse(self, relative_path: str) -> bool:
      """
      Checks for the existence of a file using advanced search methods.
      Args:
          relative_path(str): The relative path or filename to search for.
      Behavior:
          - Uses FileHunter and FileHunter_inverse to determine existence.
          - Returns True if found, False otherwise.
      Example:
          >>> from py_me import os_me
          >>> os_me.path.FileHunter_TrueOrFalse("config.txt")
          True  # or False
      Returns:
          bool
      """
      try:
        a = self.FileHunter(relative_path)
      except:
        a = None
      if a:
        return True
      else:
        user_home = os.path.expanduser("~")
        try:
          b = self.FileHunter_inverse(relative_path, user_home)
        except:
          b = None
        return True if b else False
    class TIMELINE():
        def get_version(path: str) -> list:
          """
    Retrieves the list of version numbers for a file's history.

    Args:
        path(str): The file path to query.

    Behavior:
        - Loads the timeline JSON and extracts versions for the path.
        - Returns empty list if no history.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.TIMELINE.get_version("my_file.txt")
        [1, 2, 3]

    Returns:
        list (version numbers)
    """
          pathh = path_class()
          versões = []
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      versões.append(snapshot["versao"])
          return versões
        def get_content(path: str) -> list:
          """
    Retrieves the list of contents from all versions of a file's history.

    Args:
        path(str): The file path to query.

    Behavior:
        - Loads the timeline JSON and extracts contents for the path.
        - Returns empty list if no history.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.TIMELINE.get_content("my_file.txt")
        ['Initial', 'Updated', 'Final']

    Returns:
        list (contents from each version)
    """
          pathh = path_class()
          conteúdos = []
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      conteúdos.append(snapshot["conteudo"])
          return conteúdos
        def get_TIMELINE(path: str) -> list:
          """
    Retrieves the full timeline (snapshots) for a file.

    Args:
        path(str): The file path to query.

    Behavior:
        - Loads the timeline JSON and returns all snapshots for the path.
        - Raises error if no history for the path.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.TIMELINE.get_TIMELINE("my_file.txt")
        [{'versao': 1, 'timestamp': '...', 'conteudo': '...'}, ...]

    Returns:
        list (snapshots)
    """
          pathh = path_class()
          timeline = []
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      timeline.append(snapshot)
              else:
                try:
                  raise OsMeError(f"no history for {path}")
                except OsMeError:
                  if pathh.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
          return timeline
        def show_TIMELINE(path: str) -> NoReturn:
          """
    Prints the full timeline details for a file.

    Args:
        path(str): The file path to query.

    Behavior:
        - Loads and prints version, timestamp, and content for each snapshot.
        - Raises error if no history.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.TIMELINE.show_TIMELINE("my_file.txt")
        # Prints formatted history

    Returns:
        None
    """
          pathh = path_class()
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  for snapshot in data[path]:
                      print(f"Versão: {snapshot['versao']}, Timestamp: {snapshot['timestamp']}\nConteúdo:\n{snapshot['conteudo']}\n{'-'*40}")
              else:
                try:
                  raise OsMeError(f"no history for {path}")
                except OsMeError:
                  if pathh.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
          else:
            try:
              raise OsMeError("no history")
            except OsMeError:
                if pathh.details.enable_rich_traceback:
                  console = Console()
                  console.print_exception()
        def del_TIMELINE(path: str) -> NoReturn:
          """
    Deletes the history for a specific file from the timeline.

    Args:
        path(str): The file path whose history to delete.

    Behavior:
        - Removes the path's entry from the timeline JSON.
        - Prints confirmation or raises error if no history.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.TIMELINE.del_TIMELINE("my_file.txt")
        history of my_file.txt was deleted

    Returns:
        None
    """
          pathh = path_class()
          if os.path.exists(pathh.details.timeline_file) and os.path.getsize(pathh.details.timeline_file) > 0:
              try:
                  with open(pathh.details.timeline_file, "r", encoding="utf-8") as f:
                      data = json.load(f)
              except json.JSONDecodeError:
                  data = {}
              if path in data:
                  del data[path]
                  with open(pathh.details.timeline_file, "w", encoding="utf-8") as f:
                      json.dump(data, f, indent=2)
                  print(f"history of {path} was deleted")
              else:
                try:
                  raise OsMeError(f"no history for {path}")
                except OsMeError:
                  if pathh.details.enable_rich_traceback:
                    console = Console()
                    console.print_exception()
          else:
            try:
              raise OsMeError("Nenhum histórico disponível.")
            except OsMeError:
                if pathh.details.enable_rich_traceback:
                  console = Console()
                  console.print_exception()
        @staticmethod
        def run_version(path: str, version: int, capture_output: bool = True) -> dict | None:
            """
    Executes the code from a specific version of a file's history.

    Args:
        path(str): The file path to query.
        version(int): The version number to execute.
        capture_output(bool optional): If True, captures stdout/stderr; defaults to True.

    Behavior:
        - Loads the content from the specified version.
        - Executes it in a basic sandbox if capturing output.
        - Raises ValueError if no history or version not found.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.TIMELINE.run_version("script.py", 1)
        {'success': True, 'output': '...', 'error': ''}

    Returns:
        dict (if capture_output=True) or None
    """
            pathh = path_class()
            timeline = pathh.details.timeline_file
        
            if not os.path.exists(timeline):
                raise ValueError("Nenhum histórico disponível")
            
            with open(timeline, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if path not in data:
                raise ValueError(f"Sem histórico para {path}")
            
            for snapshot in data[path]:
                if snapshot["versao"] == version:
                    code = snapshot["conteudo"]
                
                    if capture_output:
                        import io
                        from contextlib import redirect_stdout, redirect_stderr
                    
                        output = io.StringIO()
                        error = io.StringIO()
                    
                        with redirect_stdout(output), redirect_stderr(error):
                            try:
                                exec(code, {"__builtins__": {}})  # sandbox muito básico
                                return {"success": True, "output": output.getvalue(), "error": error.getvalue()}
                            except Exception as e:
                                try:
                                  raise OsMeError({"success": False, "output": output.getvalue(), "error": str(e)})
                                except OsMeError as f:
                                   if pathh.details.enable_rich_traceback:
                                      cursor = Console
                                      cursor.print_exception(f)
                                    
                    else:
                        exec(code)  # modo unsafe, avisar no docstring
                        return None
                
            raise ValueError(f"Versão {version} não encontrada")
        def del_all() -> NoReturn:
          """
    Deletes all history from the timeline file.

    Args:
        None

    Behavior:
        - Overwrites the timeline JSON with an empty dictionary.

    Example:
        >>> from py_me import os_me
        >>> os_me.path.TIMELINE.del_all()

    Returns:
        None
    """
          pathh = path_class()
          data = {}
          with open(pathh.details.timeline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
          
      
class os_me:
  """os_me is a sophisticated audio manipulation module
  that features a modifiable language,
  logging system, and versioning.
  
  classes:
  - details
  - file
  - path
    -TIMELINE
  
  def:
  - create_dir_tree
  """
  details = Details()
  file = file_class(details)
  path = path_class(details)

  def create_dir_tree(
    tree: Dict[str, Union[Dict, None, str, Path]],
    name: Optional[str] = None,
    level: int = 0,
    root: Optional[Path | str] = None,
    *,
    allow_unsafe_names: bool = False,      # default False
    create_leaf_files: bool = False,      
    exist_ok: bool = True,
) -> Path:
    """
    Creates a directory tree (folder structure) on the filesystem from a nested dictionary.

    Args:
        tree (Dict[str, Union[Dict, None, str, Path]]): Nested dictionary representing the folder structure.
            - Keys become folder/file names
            - Values that are dicts become subfolders (recursive)
            - Values that are None/str/Path become leaf files (if create_leaf_files=True)
        name (Optional[str]): Name of the root folder. If None, tries to guess the variable name using inspect.
        level (int, optional): Current recursion depth (internal use, default=0).
        root (Optional[Path | str]): Base path where the tree will be created. Defaults to current working directory.
        allow_unsafe_names (bool, optional): Allow raw/unsafe folder names (potential path traversal risk). Default=False.
        create_leaf_files (bool, optional): Create actual files for leaf nodes (None → empty file, str → file with content). Default=False.
        exist_ok (bool, optional): If True, won't raise error if directories already exist. Default=True.

    Behavior:
        - Sanitizes folder names by default to prevent path traversal and invalid characters
        - Attempts to infer root folder name from caller's local variable if 'nome' is None
        - Creates directories recursively following the dict structure
        - Optionally creates empty or content-filled files for non-dict leaf values
        - Raises RuntimeError if root directory cannot be created
        - Prints warnings on per-item creation failures (but continues)

    Example:
        >>> structure = {
        ...     "projeto": {
        ...         "src": {"main.py": "# Entrypoint"},
        ...         "tests": {}
        ...     }
        ... }
        >>> create_dir_tree(structure, create_leaf_files=True)
        PosixPath('/current/dir/projeto')

        # Resulting structure:
        # projeto/
        # ├── src/
        # │   └── main.py     ← file with content "# Entrypoint"
        # └── tests/          ← empty folder

    Returns:
        Path: The resolved Path object of the root directory that was created/used.
"""
    # ── 1. Descobrir nome da raiz (se não foi passado) ───────────────────────
    if name is None:
        try:
            frame = inspect.currentframe()
            if frame is None or frame.f_back is None:
                name = "structure" #nivel
            else:
                caller_frame = frame.f_back
                # Procuramos em locals do caller
                matches = [
                    var_name for var_name, obj in caller_frame.f_locals.items()
                    if obj is tree
                ]
                if len(matches) == 1:
                    name = matches[0]
                elif len(matches) > 1:
                    # ambíguo → usa o primeiro + sufixo pra evitar colisão
                    name = f"{matches[0]}_tree"
                else:
                    # não achou → fallback
                    name = "structure"
        except Exception:
            name = "structure"

    # Sanitiza o nome da raiz (proteção mínima contra path traversal)
    name = re.sub(r'[\\/:*?"<>|]', '_', str(name)).strip('_.- ')
    if not name:
        name = "structure"

    # ── 2. Definir pasta raiz ────────────────────────────────────────────────
    base_path = Path.cwd() if root is None else Path(root)
    root_path = base_path / name

    try:
        root_path.mkdir(parents=True, exist_ok=exist_ok)
    except Exception as e:
        raise OsMeError(f"error: {e}") from e

    # ── 3. Função recursiva principal ────────────────────────────────────────
    def _recurse(subtree: dict, current: Path, depth: int):
        for key, value in subtree.items():
            # Sanitização forte do nome (por padrão)
            if not allow_unsafe_names:
                key = re.sub(r'[\\/:*?"<>|]', '_', str(key)).strip('_.- ')
                if not key or key in {".", ".."}:
                    continue

            target = current / key

            if isinstance(value, dict):
                try:
                    target.mkdir(exist_ok=exist_ok)
                    _recurse(value, target, depth + 1)
                except Exception as e:
                    raise OsMeError(f"  └─ Error  {target}: {e}")
            else:
                # Folha: cria apenas a pasta pai (ou arquivo, se ativado)
                target.parent.mkdir(parents=True, exist_ok=exist_ok)

                if create_leaf_files:
                    try:
                        if value is None or value == "":
                            target.touch(exist_ok=exist_ok)
                        elif isinstance(value, str):
                            target.write_text(value, encoding="utf-8")
                        # poderia adicionar mais tipos (bytes, etc.)
                    except Exception as e:
                        raise OsMeError(f"  └─ Error {target}: {e}")

    _recurse(tree, root_path, level)

    return root_path