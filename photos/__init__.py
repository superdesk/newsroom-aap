from flask import current_app as app


def set_photo_coverage_href(coverage, planning_item):
    if app.config.get('PHOTO_URL') and \
            coverage['planning']['g2_content_type'] == 'picture' and \
            coverage['workflow_status'] == 'completed':
        slugline = coverage.get('planning', {}).get('slugline', planning_item.get('slugline'))
        q = '{"DateRange":[{"Start":"%s"}],"DateCreatedFilter":"true"}' % coverage['planning']['scheduled'][:10]
        return '{}"{}"?q={}'.format(app.config.get('PHOTO_URL'), slugline, q)


def init_app(app):
    app.set_photo_coverage_href = set_photo_coverage_href
