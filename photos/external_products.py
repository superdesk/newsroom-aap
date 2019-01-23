def register_products(app):
    app.sidenav('Photos', icon='coverage-photo',
                url=app.config.get('MULTIMEDIA_WEBSITE_URL'), group=2)
    app.sidenav('Videos', icon='coverage-video', group=2,
                url=app.config.get('VIDEOS_WEBSITE_URL'))
    app.sidenav('Explainers', icon='explainer',
                url=app.config.get('EXPLAINERS_WEBSITE_URL'), group=2)
    app.sidenav('CrossCheck', icon='fact-check',
                url=app.config.get('FACTCHECK_WEBSITE_URL'), group=2)
