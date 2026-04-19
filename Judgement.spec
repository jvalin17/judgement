# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['desktop/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('backend/app/game/rounds', 'backend/app/game/rounds'),
        ('backend/app/analysis/personas.json', 'backend/app/analysis'),
        ('backend/app/version_info.json', 'backend/app'),
    ],
    hiddenimports=[
        # --- backend core ---
        'backend', 'backend.app', 'backend.app.main',
        'backend.app.game_manager',
        # --- models ---
        'backend.app.models', 'backend.app.models.card',
        'backend.app.models.player', 'backend.app.models.game',
        'backend.app.models.events', 'backend.app.models.session',
        'backend.app.models.round_config',
        # --- game engine ---
        'backend.app.game', 'backend.app.game.engine',
        'backend.app.game.deck', 'backend.app.game.scorer',
        'backend.app.game.trick_resolver', 'backend.app.game.validators',
        'backend.app.game.round_manager', 'backend.app.game.round_config_loader',
        # --- ai ---
        'backend.app.ai', 'backend.app.ai.base',
        'backend.app.ai.easy', 'backend.app.ai.medium',
        'backend.app.ai.hard', 'backend.app.ai.smart_hard',
        'backend.app.ai.card_play', 'backend.app.ai.hand_evaluator',
        'backend.app.ai.personality', 'backend.app.ai.opponent_model',
        # --- ai learning ---
        'backend.app.ai.learning', 'backend.app.ai.learning.neighbor_model',
        'backend.app.ai.learning.features', 'backend.app.ai.learning.decision_collector',
        # --- analysis ---
        'backend.app.analysis', 'backend.app.analysis.fingerprint',
        'backend.app.analysis.persona_loader', 'backend.app.analysis.persona_match',
        # --- api ---
        'backend.app.api', 'backend.app.api.rest',
        'backend.app.api.websocket', 'backend.app.api.schemas',
        'backend.app.api.update',
        # --- uvicorn ---
        'uvicorn', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto',
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan', 'uvicorn.lifespan.on',
        # --- websockets ---
        'websockets', 'websockets.legacy', 'websockets.legacy.server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Judgement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Judgement',
)
app = BUNDLE(
    coll,
    name='Judgement.app',
    icon='assets/icon.icns',
    bundle_identifier='com.greenleaf.judgement',
)
