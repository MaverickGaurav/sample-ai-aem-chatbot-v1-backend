"""
Theme definitions for V2
"""

THEMES = {
    'dark': {
        'name': 'Dark Mode',
        'bg': 'bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900',
        'card': 'bg-slate-800/50 backdrop-blur-xl border-slate-700',
        'text': 'text-slate-100',
        'subtext': 'text-slate-400',
        'input': 'bg-slate-700/50 border-slate-600 text-slate-100',
        'button': 'bg-blue-600 hover:bg-blue-500'
    },
    'light': {
        'name': 'Light Mode',
        'bg': 'bg-gradient-to-br from-slate-50 via-white to-slate-100',
        'card': 'bg-white/80 backdrop-blur-xl border-slate-200',
        'text': 'text-slate-900',
        'subtext': 'text-slate-600',
        'input': 'bg-white border-slate-300 text-slate-900',
        'button': 'bg-blue-500 hover:bg-blue-600'
    },
    'aurora': {
        'name': 'Aurora Theme',
        'bg': 'bg-gradient-to-br from-purple-900 via-violet-900 to-fuchsia-900',
        'card': 'bg-white/10 backdrop-blur-2xl border-white/20',
        'text': 'text-white',
        'subtext': 'text-purple-200',
        'input': 'bg-white/10 border-white/20 text-white placeholder-purple-300',
        'button': 'bg-gradient-to-r from-pink-500 to-violet-500 hover:from-pink-600 hover:to-violet-600'
    }
}