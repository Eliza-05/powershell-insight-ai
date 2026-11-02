"""Closed, versioned rule conditions over recognized invocations and verified operands."""

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from .extraction import Atom, Extractor, Invocation


@dataclass(frozen=True)
class RuleSpec:
    rule_id: str
    behavior_id: str
    description: str
    positive: str
    negative: str
    minimum_evidence: str
    limitation: str


RULES = {r.rule_id: r for r in [
    RuleSpec("BD-B01-WEBGET", "B01", "Obtención HTTP de contenido remoto.",
             "Invoke-WebRequest/Invoke-RestMethod, URI HTTP(S) explícita y método GET o ausente.",
             "URL aislada, HEAD, método desconocido o argumento dinámico.", "Invocación y URI vinculada; método si es explícito.",
             "No alias, FTP, BITS, redirecciones ni contenido remoto recuperado."),
    RuleSpec("BD-B01-WEBCLIENT", "B01", "Descarga mediante un receptor WebClient explícito.",
             "(New-Object [System.]Net.WebClient).DownloadString/DownloadFile con URI HTTP(S).",
             "Tipo desconocido, método solo mencionado, receptor guardado en variable o URI desconocida.",
             "Receptor, método y URI; destino literal para DownloadFile.", "No seguimiento de objetos ni métodos arbitrarios."),
    RuleSpec("BD-B02-IEX", "B02", "Invocación explícita de un evaluador de texto como código.",
             "IEX/Invoke-Expression con cadena no vacía verificada o DownloadString HTTP(S) inmediato.",
             "Texto no invocado, lanzador EncodedCommand, &, wrapper declarado o entrada desconocida.",
             "Invocación y entrada vinculada; receptor/URI cuando procede.",
             "No prueba validez del código, ejecución efectiva o procedencia funcional de un wrapper no declarado."),
    RuleSpec("BD-B03-RUNWRITE", "B03", "Escritura de valor en una clave de inicio Run/RunOnce.",
             "New-ItemProperty/Set-ItemProperty con ruta HKCU/HKLM Run/RunOnce, nombre y valor no vacíos.",
             "Consulta, clave parecida, valor/ruta desconocidos o tipo no textual.",
             "Operación de escritura, ruta, nombre y valor relacionados.", "No tareas, servicios, WMI ni validación del ejecutable."),
    RuleSpec("BD-B04-DEFENDER-DISABLE", "B04", "Solicitud de desactivación de protección en tiempo real.",
             "Set-MpPreference -DisableRealtimeMonitoring $true.", "Consulta, $false, cadena o valor desconocido.",
             "Operación y booleano literal de desactivación.", "No afirma éxito frente a políticas o Tamper Protection."),
    RuleSpec("BD-B04-DEFENDER-EXCLUSION", "B04", "Adición de una exclusión de protección.",
             "Add-MpPreference -ExclusionPath con valor estático no vacío.", "Consulta, eliminación o ruta desconocida.",
             "Operación y exclusión vinculada.", "No se consulta el sistema ni se comprueba que la ruta exista."),
    RuleSpec("BD-B04-FIREWALL-DISABLE", "B04", "Solicitud de desactivación de un perfil de firewall.",
             "Set-NetFirewallProfile -Enabled $false; Profile opcional Domain/Private/Public estático.",
             "$true, consulta, perfil o booleano desconocido.",
             "Operación, booleano literal y perfil cuando se especifica.",
             "Solo perfil único literal opcional; no arrays ni reglas individuales."),
    RuleSpec("BD-B05-HOSTQUERY", "B05", "Consulta explícita de información del host.",
             "Get-Process/Get-Service/Get-ComputerInfo/Get-NetIPConfiguration/Get-MpComputerStatus/Get-MpPreference.",
             "Palabras en texto/comentarios o comandos en argumentos literales.", "Invocación en posición de comando.",
             "No infiere intención; no resuelve funciones/alias que oculten cmdlets."),
    RuleSpec("BD-B05-RUNQUERY", "B05", "Consulta de una clave de inicio automático.",
             "Get-ItemProperty con ruta Run/RunOnce estática.", "Ruta desconocida o mero literal.",
             "Consulta y ruta vinculada.", "No etiqueta como persistencia una lectura."),
    RuleSpec("BD-B06-HTTP-SEND", "B06", "Envío HTTP de datos explícitos.",
             "Invoke-WebRequest/Invoke-RestMethod, POST/PUT/PATCH, URI HTTP(S) y Body no vacío.",
             "GET, URL aislada, cuerpo desconocido o método no admitido.",
             "Operación, URI, método y cuerpo relacionados.", "No afirma exfiltración ni C2; no interpreta la respuesta como descarga B01."),
    RuleSpec("BD-B06-CONNECTIVITY", "B06", "Prueba explícita de conectividad.",
             "Test-NetConnection con destino literal o recuperado.", "Destino desconocido o mención textual.",
             "Operación y destino vinculado.", "No sockets, sesiones remotas, DNS como canal ni APIs cloud."),
    RuleSpec("BD-B07-STORED-CREDENTIAL", "B07", "Acceso solicitado a credenciales almacenadas.",
             "Get-StoredCredential con Target estático no vacío.", "Get-Credential, variable password, target desconocido o texto no invocado.",
             "Operación de lectura del almacén y target vinculado.",
             "Supone el cmdlet CredentialManager; no prueba presencia del módulo, extracción ni autorización."),
]}


@dataclass(frozen=True)
class Decision:
    rule_id: str
    supported: bool
    reason: str
    atoms: tuple[tuple[str, Atom], ...] = ()
    conditions: tuple[str, ...] = ()


RUN_KEY = re.compile(r"(?:(?:hkcu|hklm):|registry::(?:hkey_current_user|hkey_local_machine))"
                     r"\\software\\microsoft\\windows\\currentversion\\run(?:once)?\\?", re.IGNORECASE)
HOST_QUERIES = {"get-process", "get-service", "get-computerinfo", "get-netipconfiguration",
                "get-mpcomputerstatus", "get-mppreference"}


def remote(atom: Atom | None) -> bool:
    if atom is None or not atom.value or any(c.isspace() or ord(c) < 33 or ord(c) == 127 for c in atom.value):
        return False
    try:
        uri = urlsplit(atom.value)
        # Accessing port validates its syntax/range; hostname alone does not.
        _ = uri.port
        return uri.scheme.casefold() in {"http", "https"} and bool(uri.hostname)
    except ValueError:
        return False


def nonempty(atom):
    return atom is not None and atom.value is not None and bool(atom.value.strip())


def argument(call, name, position=None):
    if name in call.parameters:
        # A positional and named first operand together are ambiguous in this subset.
        if position == 0 and call.positional:
            return None
        return call.parameters[name]
    return call.positional[position] if position is not None and len(call.positional) > position else None


def decision(rule, condition, atoms, *conditions):
    return Decision(rule, bool(condition), "Condiciones estáticas suficientes." if condition else
                    "Falta una relación o argumento estático requerido; no se confirma el comportamiento.",
                    tuple((role, atom) for role, atom in atoms if atom is not None), tuple(conditions))


def evaluate(call: Invocation, extractor: Extractor) -> list[Decision]:
    name = (call.name.value or "").casefold()
    valid = call.valid_arguments
    params = call.parameters
    if call.receiver is not None:
        if name not in {"downloadstring", "downloadfile"}:
            return []
        uri = argument(call, "-uri", 0)
        dest = argument(call, "-destination", 1)
        count = 1 if name == "downloadstring" else 2
        return [decision("BD-B01-WEBCLIENT", valid and len(call.positional) == count and remote(uri)
                         and (count == 1 or nonempty(dest)),
                         [("receiver", call.receiver), ("argument", uri)] + ([("argument", dest)] if count == 2 else []),
                         "Receptor WebClient explícito.", "Método de descarga y URI HTTP(S) en la misma expresión.")]
    if name in {"invoke-webrequest", "invoke-restmethod"}:
        uri = argument(call, "-uri", 0)
        method = params.get("-method")
        verb = method.value.casefold() if method and method.value else ("get" if method is None else "unknown")
        valid = valid and len(call.positional) <= 1 and set(params) <= {
            "-uri", "-method", "-outfile", "-body", "-usebasicparsing", "-credential", "-headers"}
        if verb == "get":
            return [decision("BD-B01-WEBGET", valid and remote(uri), [("argument", uri), ("argument", method)],
                             "Operación HTTP GET (implícito o explícito).", "Origen HTTP(S) estático vinculado.")]
        body = params.get("-body")
        return [decision("BD-B06-HTTP-SEND", valid and verb in {"post", "put", "patch"} and remote(uri) and nonempty(body),
                         [("argument", uri), ("argument", method), ("argument", body)],
                         "Envío HTTP con método y cuerpo explícitos.")]
    if name in {"iex", "invoke-expression"}:
        content = argument(call, "-command", 0)
        valid = valid and len(call.positional) <= 1 and set(params) <= {"-command"}
        if valid and nonempty(content):
            return [decision("BD-B02-IEX", True, [("execution_input", content)],
                             "Evaluador de código invocado con una cadena estática no vacía.")]
        input_groups = call.arguments[1:] if set(params) == {"-command"} else call.arguments
        if valid and len(input_groups) == 1:
            method = extractor.method(list(input_groups[0]))
            if method and method.name.value == "downloadstring" and len(method.positional) == 1 and remote(method.positional[0]):
                return [decision("BD-B02-IEX", True,
                                 [("execution_input", Atom(method.start, method.end, None)),
                                  ("receiver", method.receiver), ("argument", method.positional[0])],
                                 "Entrada del evaluador es el DownloadString remoto inmediato, sin saltos de flujo.")]
        return [decision("BD-B02-IEX", False, [], "No se inventa el contenido recibido por el evaluador.")]
    if name in {"new-itemproperty", "set-itemproperty", "get-itemproperty"}:
        path, label, value = params.get("-path"), params.get("-name"), params.get("-value")
        is_run = nonempty(path) and RUN_KEY.fullmatch(path.value) is not None
        if name == "get-itemproperty":
            return [decision("BD-B05-RUNQUERY", valid and not call.positional and is_run and set(params) <= {"-path", "-name"},
                             [("argument", path)], "Lectura, sin operación de escritura.")]
        kind = params.get("-propertytype")
        return [decision("BD-B03-RUNWRITE", valid and not call.positional and is_run and nonempty(label) and nonempty(value)
                         and (kind is None or kind.value and kind.value.casefold() in {"string", "expandstring"})
                         and set(params) <= {"-path", "-name", "-value", "-propertytype", "-force"},
                         [("argument", path), ("argument", label), ("argument", value)],
                         "Escritura en Run/RunOnce de HKCU/HKLM.", "Nombre y valor de inicio estáticos en la misma invocación.")]
    if name in {"set-mppreference", "set-netfirewallprofile"}:
        defender = name == "set-mppreference"
        key, expected = ("-disablerealtimemonitoring", "true") if defender else ("-enabled", "false")
        value = params.get(key)
        rule = "BD-B04-DEFENDER-DISABLE" if defender else "BD-B04-FIREWALL-DISABLE"
        if value and value.kind == "boolean" and value.value != expected:
            return []  # Restoration/enabling is deliberately not labeled as weakening.
        allowed = {key} if defender else {key, "-profile"}
        profile = params.get("-profile")
        profile_valid = profile is None or (nonempty(profile) and profile.value.casefold() in {"domain", "private", "public"})
        return [decision(rule, valid and not call.positional and set(params) <= allowed and value is not None
                         and value.kind == "boolean" and value.value == expected and profile_valid,
                         [("argument", value), ("argument", profile)],
                         "Booleano literal solicita debilitar el control; perfil estático cuando se especifica, sin afirmar éxito.")]
    if name == "add-mppreference":
        path = params.get("-exclusionpath")
        return [decision("BD-B04-DEFENDER-EXCLUSION", valid and not call.positional and set(params) == {"-exclusionpath"}
                         and nonempty(path), [("argument", path)], "Adición explícita de exclusión de protección.")]
    if name in HOST_QUERIES:
        return [decision("BD-B05-HOSTQUERY", valid, [], "Consulta explícita en posición de comando.")]
    if name == "test-netconnection":
        target = argument(call, "-computername", 0)
        return [decision("BD-B06-CONNECTIVITY", valid and len(call.positional) <= 1 and nonempty(target)
                         and set(params) <= {"-computername", "-port", "-informationlevel"},
                         [("argument", target)], "Prueba de conectividad con destino explícito.")]
    if name == "get-storedcredential":
        target = argument(call, "-target", 0)
        return [decision("BD-B07-STORED-CREDENTIAL", valid and len(call.positional) <= 1 and nonempty(target)
                         and set(params) <= {"-target", "-ascredentialobject"},
                         [("argument", target)], "Lectura explícita del almacén de credenciales, con target vinculado.")]
    return []
