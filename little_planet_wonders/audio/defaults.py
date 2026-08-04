from __future__ import annotations

from typing import Any


VOICE_DEFAULTS: dict[str, dict[str, Any]] = {
    "roxana": {
        "id": "roxana",
        "display_name": "Roxana",
        "voice_identity": {
            "language": "Persian",
            "secondary_language": "English",
            "apparent_age": "late twenties",
            "pitch": "medium-low",
            "timbre": "warm and slightly husky",
            "speaking_speed": "slow to moderate",
            "vocal_energy": "restrained",
            "articulation": "clear",
            "emotional_baseline": "calm and observant",
        },
        "performance": {
            "default_volume": "quiet",
            "pause_style": "deliberate",
            "breathing": "subtle",
            "emotional_expression": "controlled",
            "laughter": "rare and quiet",
            "shouting": "avoid unless explicitly required",
        },
        "consistency_constraints": [
            "preserve the same vocal age",
            "preserve the same accent",
            "preserve speaking speed",
            "do not randomly increase vocal energy",
            "do not change voice identity between scenes",
        ],
        "generation": {
            "provider": "local-tts",
            "model": "configured-model-name",
            "voice_id": "roxana-v1",
            "default_seed": 843121,
        },
        "references": {
            "neutral": "audio-assets/voice-references/roxana-neutral.wav",
            "emotional": "audio-assets/voice-references/roxana-emotional.wav",
            "whisper": "audio-assets/voice-references/roxana-whisper.wav",
        },
    },
    "shakiba": {
        "id": "shakiba",
        "display_name": "Shakiba",
        "voice_identity": {
            "language": "Persian",
            "pitch": "medium",
            "timbre": "clear and bright",
            "speaking_speed": "moderate",
            "vocal_energy": "confident",
            "articulation": "precise",
            "emotional_baseline": "focused",
        },
        "performance": {
            "default_volume": "conversational",
            "pause_style": "short",
            "breathing": "natural",
            "emotional_expression": "more expressive than Roxana",
        },
        "consistency_constraints": [
            "preserve vocal brightness",
            "preserve pronunciation style",
            "keep the voice clearly distinct from Roxana",
            "do not merge Roxana and Shakiba voice profiles",
        ],
        "generation": {
            "provider": "local-tts",
            "model": "configured-model-name",
            "voice_id": "shakiba-v1",
            "default_seed": 334921,
        },
    },
}


PRONUNCIATION_DEFAULTS = {
    "entries": {
        "Roxana": {"language": "Persian", "phonetic": "rok-saa-naa"},
        "Shakiba": {"language": "Persian", "phonetic": "sha-ki-baa"},
        "Wan": {"language": "English", "phonetic": "wahn"},
        "MCP": {"language": "English", "spoken_form": "M C P"},
    },
    "rules": [
        "numbers must be expanded before voice generation",
        "abbreviations must have an explicit spoken form",
        "character names must always use dictionary pronunciation",
        "technical terms must not switch pronunciation between scenes",
    ],
}


DIALOGUE_DEFAULTS = {
    "sample_rate": 48000,
    "bit_depth": 24,
    "channel_format": "mono",
    "naturalism": {
        "preserve_breathing": True,
        "preserve_short_pauses": True,
        "remove_long_accidental_silence": True,
        "avoid_robotic_timing": True,
    },
    "timing": {
        "minimum_pause_between_sentences_ms": 250,
        "maximum_unplanned_silence_ms": 1000,
        "dialogue_pre_roll_ms": 150,
        "dialogue_post_roll_ms": 250,
    },
    "performance": {
        "acting_style": "restrained cinematic realism",
        "avoid_exaggerated_emotion": True,
        "match_scene_emotional_state": True,
    },
    "lip_sync": {
        "generate_final_audio_before_video": True,
        "preserve_word_timing": True,
        "never_replace_audio_after_final_lip_sync": True,
    },
}


MUSIC_DEFAULTS = {
    "identity": {
        "genre": ["cinematic ambient", "restrained electronic", "minimal orchestral"],
        "emotional_character": ["mysterious", "melancholic", "tense"],
        "instrumentation": {
            "primary": ["low synthesizer pads", "processed piano", "soft strings"],
            "secondary": [
                "restrained percussion",
                "low electronic pulses",
                "distant metallic textures",
            ],
        },
        "forbidden": [
            "upbeat pop drums",
            "heroic brass",
            "aggressive trailer impacts",
            "cheerful melodies",
            "excessive orchestration",
        ],
    },
    "tempo": {"default_bpm": 72, "tension_range_bpm": {"minimum": 75, "maximum": 92}},
    "harmony": {
        "default_mode": "minor",
        "complexity": "moderate",
        "avoid_clear_happy_resolutions": True,
    },
    "mixing": {
        "dialogue_ducking_db": -6,
        "maximum_music_true_peak_db": -3,
        "preserve_low_frequency_space_for_dialogue": True,
    },
    "themes": {
        "roxana": {
            "motif": "three descending piano notes",
            "instruments": ["processed piano", "low synth pad"],
        },
        "shakiba": {
            "motif": "short rising string phrase",
            "instruments": ["soft strings", "granular texture"],
        },
        "danger": {
            "motif": "low repeating electronic pulse",
            "tempo_bpm": 86,
        },
    },
}


SOUND_EFFECT_DEFAULTS = {
    "style": {
        "realism": "grounded",
        "intensity": "restrained",
        "perspective_sensitive": True,
        "match_environment_acoustics": True,
    },
    "categories": {
        "footsteps": {
            "rooftop": {
                "surface": "wet concrete",
                "asset_set": "wet-concrete-boots",
                "variation_policy": "round-robin",
                "minimum_repeat_distance": 4,
            }
        },
        "doors": {
            "rooftop_maintenance_door": {
                "material": "heavy metal",
                "open_asset": "maintenance-door-open.wav",
                "close_asset": "maintenance-door-close.wav",
            }
        },
        "devices": {
            "black_data_device": {
                "activate_asset": "device-activate-soft.wav",
                "alert_asset": "device-alert-muted.wav",
            }
        },
        "weather": {
            "rain_on_jacket": {
                "asset": "rain-on-leather-close.wav",
                "use_only_in_closeups": True,
            }
        },
    },
    "rules": [
        "use sound based on visible action",
        "use distance-appropriate volume",
        "do not add an impact when no impact is visible",
        "avoid repeating the identical sound sample",
        "preserve the established material sound",
    ],
}


MIXING_DEFAULTS = {
    "technical": {
        "sample_rate": 48000,
        "delivery_channels": "stereo",
        "maximum_true_peak_db": -1,
    },
    "loudness": {"web_target_lufs": -16, "cinematic_preview_lufs": -18},
    "priority": [
        "dialogue",
        "important narrative sound effects",
        "ambience",
        "music",
        "decorative sound effects",
    ],
    "dialogue": {
        "center_pan": True,
        "compression": "subtle",
        "noise_reduction": "light",
        "de_esser": "light",
    },
    "music": {"duck_under_dialogue": True, "ducking_db": -6, "attack_ms": 100, "release_ms": 500},
    "ambience": {
        "crossfade_between_scenes_ms": 600,
        "maintain_room_tone_during_dialogue": True,
    },
    "sound_effects": {"maximum_simultaneous_prominent_effects": 3},
    "stereo": {"dialogue_width": 0, "music_width": 80, "ambience_width": 100},
}


AUDIO_DEFAULTS = {
    "audio_style": {"dialogue": DIALOGUE_DEFAULTS},
    "music": MUSIC_DEFAULTS,
    "sound_effects": SOUND_EFFECT_DEFAULTS,
    "mixing": MIXING_DEFAULTS,
    "pronunciation": PRONUNCIATION_DEFAULTS,
    "ambience": {},
    "audio": {},
}
