import cycler
import matplotlib as mpl
import matplotlib.pyplot as plt
    
class Colors:
    # --- Blues (cool & clean) ---
    blue1 = '#0a3d62'   # deep navy
    blue2 = '#3c6382'   # muted ocean blue
    blue3 = '#60a3bc'   # light teal-blue
    blue4 = '#c8dce3'   # pale blue-gray

    # --- Greens (fresh & natural) ---
    green1 = '#2e7d32'  # deep forest green
    green2 = '#43a047'  # balanced natural green
    green3 = '#66bb6a'  # medium soft green
    green4 = '#a5d6a7'  # pale mint green
    
    # --- Grays (neutral and balanced) ---
    gray1 = '#424242'   # extra dark gray
    gray2 = '#616161'   # dark slate gray
    gray3 = '#9e9e9e'   # medium gray
    gray4 = '#e0e0e0'   # light neutral gray
    
    # --- Reds (rich & elegant) ---
    red1 = '#b71c1c'    # strong crimson
    red2 = '#d32f2f'    # vibrant red
    red3 = '#ef5350'    # soft coral red
    red4 = '#ffcdd2'    # pale rose red

    # --- Yellows (warm & subtle) ---
    yellow1 = '#f9a825'  # amber yellow
    yellow2 = '#fbc02d'  # golden yellow
    yellow3 = '#fdd835'  # bright lemon yellow
    yellow4 = '#fff176'  # pastel yellow
    
    # --- Oranges (warm gradient) ---
    orange1 = '#ef6c00'  # deep orange
    orange2 = '#fb8c00'  # medium orange
    orange3 = '#ffb74d'  # light orange
    orange4 = '#ffe0b2'  # soft peach

    # --- Purples (modern & rich) ---
    purple1 = '#4a148c'  # deep violet
    purple2 = '#7b1fa2'  # rich purple
    purple3 = '#ba68c8'  # soft lavender
    purple4 = '#e1bee7'  # pale violet

    # --- Teals (balanced between blue & green) ---
    teal1 = '#00695c'    # deep teal
    teal2 = '#00897b'    # medium teal
    teal3 = '#26a69a'    # light teal
    teal4 = '#80cbc4'    # pale aqua

    # --- Browns (earth tones) ---
    brown1 = '#4e342e'   # dark brown
    brown2 = '#6d4c41'   # medium brown
    brown3 = '#8d6e63'   # light brown
    brown4 = '#d7ccc8'   # beige tone

    # --- Pinks (vibrant & modern) ---
    pink1 = '#880e4f'    # rich magenta
    pink2 = '#c2185b'    # bold pink
    pink3 = '#f06292'    # light rose
    pink4 = '#f8bbd0'    # pale blush

    # --- Cyans (clean & refreshing) ---
    cyan1 = '#006064'    # dark cyan
    cyan2 = '#00838f'    # medium cyan
    cyan3 = '#26c6da'    # bright cyan
    cyan4 = '#b2ebf2'    # soft cyan tint

plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['mathtext.fontset'] = 'stix'
colors = [Colors.blue3, Colors.red2, Colors.green2, Colors.yellow1, Colors.purple2, Colors.teal1, Colors.pink3, Colors.brown2, Colors.cyan3]
cyl = cycler.cycler('color', colors)
plt.rcParams['axes.prop_cycle'] = cyl

mpl.rcParams['font.size'] = 9
mpl.rcParams['lines.linewidth'] = 2
mpl.rcParams['lines.color'] = 'black'
mpl.rcParams['patch.edgecolor'] = 'white'
mpl.rcParams['axes.grid.which'] = 'major'
mpl.rcParams['lines.markersize'] = 1.6
mpl.rcParams['ytick.labelsize'] = 8
mpl.rcParams['xtick.labelsize'] = 8
mpl.rcParams['ytick.labelright'] = False
mpl.rcParams['xtick.labeltop'] = False
mpl.rcParams['ytick.right'] = True
mpl.rcParams['xtick.top'] = True
mpl.rcParams['ytick.major.right'] = True
mpl.rcParams['xtick.major.top'] = True
mpl.rcParams['axes.labelweight'] = 'normal'
mpl.rcParams['legend.fontsize'] = 8
mpl.rcParams['legend.framealpha']= 0.5
mpl.rcParams['axes.titlesize'] = 12
mpl.rcParams['axes.titleweight'] ='normal'
mpl.rcParams['font.family'] ='TImes New Roman'
mpl.rcParams['axes.labelsize'] = 10
mpl.rcParams['axes.linewidth'] = 1.25
mpl.rcParams['xtick.major.size'] = 5.0
mpl.rcParams['xtick.minor.size'] = 3.0
mpl.rcParams['ytick.major.size'] = 5.0
mpl.rcParams['ytick.minor.size'] = 3.0

alpha = 0.7
to_rgba = mpl.colors.ColorConverter().to_rgba
mpl.rcParams['xtick.direction'] = 'in'
mpl.rcParams['ytick.direction'] = 'in' 

def subplots(figwidth=14, figheight=10, nrows=1, ncols=1, sharex=False, sharey=False):
    figwidth = figwidth / 2.54  # convert cm to inches
    figheight = figheight / 2.54  # convert cm to inches        
    
    fig, ax = plt.subplots(figsize=(figwidth,figheight), nrows=nrows, ncols=ncols, sharex=sharex, sharey=sharey)
    axs = [ax] if nrows*ncols==1 else ax
    for a in axs:
        a.grid(alpha=0.25)        
    return fig, ax