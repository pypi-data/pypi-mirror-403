# @Compile : True
from aixm.utils import *
import os
import uuid

try:
    import matplotlib.pyplot as plt
except:
    plt = None

os.makedirs(relative_data_path('files/charts'), exist_ok=True)


def draw_histogram(data):
    if plt is None:
        return ''
    keys = [item['key'] for item in data['counts']] + ['其他']
    counts = [item['count'] for item in data['counts']] + [data['other']]
    plt.figure(figsize=(12, 7))
    bars = plt.bar(keys, counts, color='skyblue')
    plt.ylabel('')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2, yval, int(yval), ha='center', va='bottom')
    fig_path = relative_data_path('files/charts', str(uuid.uuid4()) + '.png')

    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    return fig_path.replace(relative_data_path('files'), '/files')


def draw_pie(data):
    if plt is None:
        return ''

    keys = [item['key'] for item in data['counts']] + ['其他']
    counts = [item['count'] for item in data['counts']] + [data['other']]

    def make_autopct(values):
        def my_autopct(pct):
            total = sum(values)
            val = int(round(pct * total / 100.0))
            return f'{pct:.1f}%\n({val})'

        return my_autopct

    plt.figure(figsize=(10, 7))
    plt.pie(counts, labels=keys, autopct=make_autopct(counts), startangle=140)
    plt.tight_layout()

    fig_path = relative_data_path('files/charts', str(uuid.uuid4()) + '.png')

    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    return fig_path.replace(relative_data_path('files'), '/files')
