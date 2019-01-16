def register_products(app):
    app.sidenav('Photos', icon='coverage-photo',
                url='https://photos.aap.com.au/', group=2)
    app.sidenav('Videos', icon='coverage-video', group=2,
                url='https://photos.aap.com.au/galleries/Newsroom/Video')
    app.sidenav('Explainers', icon='explainer',
                url='https://photos.aap.com.au/search/(supplementalcategory'
                    ':VIDEXP)/Visual%20Explainers', group=2)
    app.sidenav('Fact Check', icon='fact-check',
                url='https://crosscheck.aap.com.au/', group=2)
