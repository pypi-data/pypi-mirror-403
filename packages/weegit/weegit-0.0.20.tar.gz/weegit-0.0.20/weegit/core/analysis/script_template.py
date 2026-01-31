TEMPLATE = """from pathlib import Path
from weegit.core.weegit_session import WeegitSessionManager, UserSession

# Init session
session = WeegitSessionManager()
OUT_WEEGIT_FOLDER = Path(r"{out_weegit_folder}")
session.init_from_folder(OUT_WEEGIT_FOLDER)

# Work with data
print(session.experiment_data.header)
sweep_idx, start_point, end_point = 0, 0, 10_000
for ch_idx in range(session.experiment_data.header.number_of_channels):
    channel_data = session.experiment_data.data_memmaps[ch_idx][sweep_idx][start_point:end_point]
    print(f"Channel {{session.experiment_data.header.channel_info.name[ch_idx]}} max voltage val: ",
          max(session.experiment_data.from_int16_to_voltage_val(channel_data, ch_idx)))

# Work with GUI session
session_filename = UserSession.session_name_to_filename("{session_name}")
session.switch_sessions(session_filename)
print(session.current_user_session.gui_setup)

{events_block}
{spikes_block}
"""

EVENTS_BLOCK = """# Work with events
for event in session.user_session.events_table:
    # skip events in period
    if "PERIOD_NAME" in getattr(event, "periods", []):
        continue
"""

SPIKES_BLOCK = """# Work with spikes
for sweep_idx, spikes in session.user_session.cached_spikes.items():
    print("Sweep", sweep_idx, "spikes:", spikes)
"""
