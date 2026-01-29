config = wiz.model("portal/season/config")

manifest = dict()
manifest['name'] = config['pwa_title']
manifest['short_name'] = config['pwa_title']
manifest['start_url'] = config['pwa_start_url']
manifest['icons'] = [
    {
        "src": config['pwa_icon'],
        "sizes": "64x64 32x32 24x24 16x16",
        "type": "image/x-icon"
    },
    {
        "src": config['pwa_icon_192'],
        "sizes": "192x192",
        "type": "image/png"
    },
    {
        "src": config['pwa_icon_512'],
        "sizes": "512x512",
        "type": "image/png"
    }
]

manifest['theme_color'] = config['pwa_theme_color']
manifest['background_color'] = config['pwa_background_color']
manifest['display'] = config['pwa_display']
manifest['orientation'] = config['pwa_orientation']

wiz.response.json(manifest)