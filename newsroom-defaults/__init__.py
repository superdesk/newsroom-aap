def init_app(app):
    for section in app.sections or []:
        if section.get('_id') == 'wire':
            section['name'] = 'The Wire'

    for sidenavs in app.sidenavs or []:
        if sidenavs.get('name') and sidenavs.get('name').lower() == 'wire':
            sidenavs['name'] = 'The Wire'
