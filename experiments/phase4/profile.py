"""Prospective profile binding; importing this module reads no reserved cases."""
from app.schemas.deobfuscation import DeobfuscationLimits
from app.services.deobfuscation.engine import deobfuscate
from app.services.llm.qwen14_prototype import PrototypeSettings
from app.services.llm.qwen14 import Qwen14Adapter, Qwen14Transport
from app.services.llm.qwen3coder import Qwen3CoderSettings, Qwen3CoderAdapter, Qwen3CoderTransport
from app.services.pipelines.context import build_context
from app.services.pipelines.provider import response_schema
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.strategy import DeterministicLayersStrategy


def settings_for(configuration):
    name = configuration.get('llm_profile', 'qwen14')
    classes = {'qwen14': PrototypeSettings, 'qwen3coder-v2': Qwen3CoderSettings}
    if name not in classes: raise ValueError('Unknown explicit Phase 4 profile')
    return classes[name].model_validate(configuration['settings'])


def profile_name(settings):
    if isinstance(settings, Qwen3CoderSettings): return 'qwen3coder-v2'
    if isinstance(settings, PrototypeSettings): return 'qwen14'
    raise TypeError('Phase 4 requires a pinned application profile')


def strategy_for(settings):
    return DeterministicLayersStrategy() if profile_name(settings) == 'qwen3coder-v2' else None


def context_for(script, mode, settings):
    if mode not in {'B', 'C'}: raise ValueError('Context mode must be B or C')
    recovery = deobfuscate(script, input_provenance='original',
        limits=DeobfuscationLimits(max_input_bytes=settings.max_input_bytes)) if mode == 'C' else None
    strategy = strategy_for(settings)
    return strategy.build_context(script, recovery) if strategy else build_context(script, recovery)


def payload_for(context, settings):
    profile_name(settings)
    return {'model': settings.model, 'messages': context.messages, 'format': response_schema(),
        'stream': False, 'truncate': False, 'keep_alive': settings.keep_alive, 'options': settings.options.model_dump()}


def transport_for(settings, *, authorize_dispatch=None, timeout=300):
    cls = Qwen3CoderTransport if profile_name(settings) == 'qwen3coder-v2' else Qwen14Transport
    return cls(authorize_dispatch=authorize_dispatch, timeout=timeout)


def service_for(settings, *, sampler, gate_factory, transport_factory):
    cls = Qwen3CoderAdapter if profile_name(settings) == 'qwen3coder-v2' else Qwen14Adapter
    adapter = cls(settings, sampler=sampler, gate_factory=gate_factory, transport_factory=transport_factory)
    return AnalysisService(settings, adapter=adapter, strategy=strategy_for(settings))
