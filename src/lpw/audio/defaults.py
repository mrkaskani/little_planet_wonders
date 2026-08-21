"""Define immutable defaults and supported values for this package."""

from __future__ import annotations

from typing import Any


VOICE_DEFAULTS: dict[str, dict[str, Any]] = {
    "riri": {
        "id": "riri",
        "display_name": "Riri",
        "voice_identity": {
            "language": "English",
            "apparent_age": "four-year-old child",
            "gender_presentation": "feminine",
            "pitch": "high",
            "timbre": "smooth, round, light, airy, and non-nasal",
            "speaking_speed": "slow and flowing",
            "vocal_energy": "gentle",
            "articulation": "clear",
            "emotional_baseline": "sweet, warm, and cheerful",
        },
        "performance": {
            "default_volume": "soft conversational",
            "pause_style": "natural and unhurried",
            "breathing": "light and natural",
            "emotional_expression": "clear and child-friendly",
            "laughter": "small and warm",
            "shouting": "forbidden",
        },
        "consistency_constraints": [
            "preserve Riri's four-year-old feminine identity",
            "preserve the high pitch and light-head resonance",
            "preserve the smooth round non-nasal airy timbre",
            "keep delivery gentle and clearly distinct from Yoyo",
        ],
        "generation": {
            "provider": "local-tts",
            "model": "configured-model-name",
            "voice_id": "riri-v1",
            "default_seed": 843121,
        },
        "references": {
            "neutral": "audio-assets/voice-references/riri-neutral.wav",
            "emotional": "audio-assets/voice-references/riri-emotional.wav",
        },
    },
    "yoyo": {
        "id": "yoyo",
        "display_name": "Yoyo",
        "voice_identity": {
            "language": "English",
            "apparent_age": "seven-to-eight-year-old child",
            "gender_presentation": "boy",
            "pitch": "low natural prepubescent-boy range",
            "timbre": "grounded, dry, chest-forward, slightly nasal and reedy",
            "speaking_speed": "quick with clear stops",
            "vocal_energy": "lively but controlled",
            "articulation": "firm and punchy",
            "emotional_baseline": "playful, curious, and energetic",
        },
        "performance": {
            "default_volume": "conversational",
            "pause_style": "short",
            "breathing": "natural",
            "emotional_expression": "bright and clearly readable",
        },
        "consistency_constraints": [
            "preserve Yoyo's boy identity and natural child pitch",
            "preserve firm consonants and quick stop-start rhythm",
            "keep the voice clearly distinct from Riri",
            "do not make the voice feminine, adult, or artificially lowered",
        ],
        "generation": {
            "provider": "local-tts",
            "model": "configured-model-name",
            "voice_id": "yoyo-v1",
            "default_seed": 334921,
        },
    },
}


PRONUNCIATION_DEFAULTS = {
    "entries": {
        "Riri": {"language": "English", "phonetic": "REE-ree"},
        "Yoyo": {"language": "English", "phonetic": "YO-yo"},
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
        "acting_style": "clear natural preschool animation",
        "avoid_excessive_emotion": True,
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
        "genre": ["warm acoustic", "playful melodic", "gentle cinematic"],
        "emotional_character": ["curious", "reassuring", "emotionally safe"],
        "instrumentation": {
            "primary": ["marimba", "soft piano", "ukulele", "gentle flute"],
            "secondary": [
                "wooden percussion",
                "light strings",
                "warm synthesizer pads",
            ],
        },
        "forbidden": [
            "horror music",
            "aggressive action music",
            "heavy bass impacts",
            "harsh electronic sounds",
            "intense suspense",
            "chaotic percussion",
            "loud orchestral hits",
            "dark threatening drones",
        ],
    },
    "tempo": {"default_bpm": 72, "tension_range_bpm": {"minimum": 75, "maximum": 92}},
    "harmony": {
        "default_mode": "major",
        "complexity": "simple",
        "prefer_clear_happy_resolutions": True,
    },
    "mixing": {
        "dialogue_ducking_db": -6,
        "maximum_music_true_peak_db": -3,
        "preserve_low_frequency_space_for_dialogue": True,
    },
    "child_safety": {
        "audience_age": "2-5",
        "maximum_energy": "moderate",
        "maximum_complexity": "simple",
        "preserve_participation_pauses": True,
        "avoid_sudden_loudness": True,
    },
    "themes": {
        "riri": {
            "motif": "high connected felt-piano arch",
            "instruments": ["felt piano", "soft glockenspiel"],
        },
        "yoyo": {
            "motif": "lower detached bounce-and-slide phrase",
            "instruments": ["celesta", "marimba"],
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
            "kindergarten_garden": {
                "surface": "soft grass and stone path",
                "asset_set": "gentle-preschool-steps",
                "variation_policy": "round-robin",
                "minimum_repeat_distance": 4,
            }
        },
        "doors": {
            "kindergarten_garden_door": {
                "material": "painted wood",
                "open_asset": "kindergarten-door-open.wav",
                "close_asset": "kindergarten-door-close.wav",
            }
        },
        "devices": {
            "learning_tablet": {
                "activate_asset": "tablet-activate-soft.wav",
                "alert_asset": "tablet-alert-gentle.wav",
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
    "child_safety": {
        "audience_age": "2-5",
        "maximum_volume": "moderate",
        "forbidden_qualities": [
            "explosive",
            "gun-like",
            "horror",
            "scream",
            "harsh alarm",
            "heavy bass impact",
            "frightening whisper",
            "realistic injury",
            "aggressive transient",
        ],
    },
}


VOICE_PRODUCTION_DEFAULTS = {
    "audience": {"minimum_age": 2, "maximum_age": 5},
    "workflow": {
        "require_exact_approved_dialogue": True,
        "require_clean_dialogue": True,
        "require_review_before_lock": True,
        "require_locked_audio_for_lip_sync": True,
    },
    "safety": {
        "maximum_emotional_intensity": 0.6,
        "require_reassuring_resolution": True,
    },
    "participation": {
        "minimum_response_pause_seconds": 3,
        "maximum_response_pause_seconds": 5,
    },
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
    "continuity": {},
    "voice_production": VOICE_PRODUCTION_DEFAULTS,
}
