import pandas as pd
from koboextractor import KoboExtractor
import streamlit as st

KOBO_TOKEN = "1ba028bb7a918cd6040a38381ff2f0b6467722b1"
kobo = KoboExtractor(KOBO_TOKEN, 'https://eu.kobotoolbox.org/api/v2')

@st.cache_data(ttl=600)
def load_dataset(option, submitted_after):
    asset_uids = {
        "Data": "aj4HuArKXwgfbyRwJWcB7b"
    }

    asset_uid = asset_uids.get(option)
    if asset_uid is None:
        return None

    # Load data from KoBoToolbox
    new_data = kobo.get_data(asset_uid, submitted_after=submitted_after)
    df = pd.DataFrame(new_data['results'])

    return df