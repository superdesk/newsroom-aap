def register_products(app):
    app.sidenav('Photos', icon='coverage-photo',
                url=app.config.get('MULTIMEDIA_WEBSITE_URL'), group=2)
    app.sidenav('FactCheck', icon='fact-check',
                url=app.config.get('FACTCHECK_WEBSITE_URL'), group=2)
