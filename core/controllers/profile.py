# Copyright 2014 The Oppia Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Controllers for the profile page."""

__author__ = 'sfederwisch@google.com (Stephanie Federwisch)'

from core.controllers import base
from core.domain import config_domain
from core.domain import user_services
import feconf
import utils


EDITOR_PREREQUISITES_AGREEMENT = config_domain.ConfigProperty(
    'editor_prerequisites_agreement', 'Html',
    'The agreement that editors are asked to accept before making any '
    'contributions.',
    default_value=feconf.DEFAULT_EDITOR_PREREQUISITES_AGREEMENT
)


class ProfilePage(base.BaseHandler):
    """The (view-only) profile page."""

    def get(self, username):
        """Handles GET requests for the publicly-viewable profile page."""
        if not username:
            raise self.PageNotFoundException

        user_settings = user_services.get_user_settings_from_username(username)
        if not user_settings:
            raise self.PageNotFoundException

        self.values.update({
            'nav_mode': feconf.NAV_MODE_PROFILE,
            'user_bio': user_settings.user_bio,
        })
        self.render_template('profile/profile.html')


class PreferencesPage(base.BaseHandler):
    """The preferences page."""

    PAGE_NAME_FOR_CSRF = 'preferences'

    @base.require_user
    def get(self):
        """Handles GET requests."""
        self.values.update({
            'nav_mode': feconf.NAV_MODE_PROFILE,
            'LANGUAGE_CODES_AND_NAMES': [{
                'code': lc['code'],
                'name': utils.get_short_language_description(
                    lc['description']),
            } for lc in feconf.ALL_LANGUAGE_CODES],
        })
        self.render_template('profile/preferences.html')


class PreferencesHandler(base.BaseHandler):
    """Provides data for the preferences page."""

    PAGE_NAME_FOR_CSRF = 'preferences'

    @base.require_user
    def get(self):
        """Handles GET requests."""
        user_settings = user_services.get_user_settings(self.user_id)
        self.values.update({
            'user_bio': user_settings.user_bio,
            'preferred_language_codes': user_settings.preferred_language_codes,
        })
        self.render_json(self.values)

    @base.require_user
    def put(self):
        """Handles POST requests."""
        update_type = self.payload.get('update_type')
        data = self.payload.get('data')

        if update_type == 'user_bio':
            user_services.update_user_bio(self.user_id, data)
        elif update_type == 'preferred_language_codes':
            user_services.update_preferred_language_codes(self.user_id, data)
        else:
            raise self.InvalidInputException(
                'Invalid update type: %s' % update_type)


class EditorPrerequisitesPage(base.BaseHandler):
    """The page which prompts for username and acceptance of terms."""

    PAGE_NAME_FOR_CSRF = 'editor_prerequisites_page'

    @base.require_user
    def get(self):
        """Handles GET requests."""
        self.values.update({
            'agreement': EDITOR_PREREQUISITES_AGREEMENT.value,
            'nav_mode': feconf.NAV_MODE_PROFILE,
        })
        self.render_template('profile/editor_prerequisites.html')


class EditorPrerequisitesHandler(base.BaseHandler):
    """Provides data for the editor prerequisites page."""

    PAGE_NAME_FOR_CSRF = 'editor_prerequisites_page'

    @base.require_user
    def get(self):
        """Handles GET requests."""
        user_settings = user_services.get_user_settings(self.user_id)
        self.render_json({
            'has_agreed_to_terms': bool(user_settings.last_agreed_to_terms),
            'username': user_settings.username,
        })

    @base.require_user
    def post(self):
        """Handles POST requests."""
        username = self.payload.get('username')
        agreed_to_terms = self.payload.get('agreed_to_terms')

        if not isinstance(agreed_to_terms, bool) or not agreed_to_terms:
            raise self.InvalidInputException(
                'In order to edit explorations on this site, you will '
                'need to accept the license terms.')
        else:
            user_services.record_agreement_to_terms(self.user_id)

        if user_services.get_username(self.user_id):
            # A username has already been set for this user.
            self.render_json({})
            return

        try:
            user_services.set_username(self.user_id, username)
        except utils.ValidationError as e:
            raise self.InvalidInputException(e)

        self.render_json({})


class UsernameCheckHandler(base.BaseHandler):
    """Checks whether a username has already been taken."""

    PAGE_NAME_FOR_CSRF = 'editor_prerequisites_page'

    @base.require_user
    def post(self):
        """Handles POST requests."""
        username = self.payload.get('username')
        try:
            user_services.UserSettings.require_valid_username(username)
        except utils.ValidationError as e:
            raise self.InvalidInputException(e)

        username_is_taken = user_services.is_username_taken(username)
        self.render_json({
            'username_is_taken': username_is_taken,
        })
