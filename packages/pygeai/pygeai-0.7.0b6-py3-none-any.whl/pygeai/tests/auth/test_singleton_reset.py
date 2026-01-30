import unittest

from pygeai.core.singleton import Singleton
from pygeai.core.base.session import Session, reset_session
from pygeai.core.common.constants import AuthType


class TestSingletonReset(unittest.TestCase):
    """
    Tests for Singleton reset functionality to ensure proper test isolation.
    
    python -m unittest pygeai.tests.auth.test_singleton_reset.TestSingletonReset
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_session()

    def tearDown(self):
        """Clean up test fixtures"""
        reset_session()

    def test_singleton_returns_same_instance(self):
        """Test that Singleton returns the same instance without reset"""
        s1 = Session(api_key="key1", base_url="https://test1.com")
        s2 = Session(api_key="key2", base_url="https://test2.com")
        
        self.assertIs(s1, s2)
        self.assertEqual(s1.api_key, "key1")
        self.assertEqual(s2.api_key, "key1")

    def test_reset_instance_clears_singleton_cache(self):
        """Test that Singleton.reset_instance clears the cache for specific class"""
        s1 = Session(api_key="key1", base_url="https://test1.com")
        self.assertEqual(s1.api_key, "key1")
        
        Singleton.reset_instance(Session)
        
        s2 = Session(api_key="key2", base_url="https://test2.com")
        
        self.assertIsNot(s1, s2)
        self.assertEqual(s2.api_key, "key2")

    def test_reset_session_clears_singleton_cache(self):
        """Test that reset_session() clears both global variable and singleton cache"""
        s1 = Session(api_key="key1", base_url="https://test1.com")
        self.assertEqual(s1.api_key, "key1")
        self.assertEqual(s1.auth_type, AuthType.API_KEY)
        
        reset_session()
        
        s2 = Session(
            base_url="https://test2.com",
            access_token="token2",
            project_id="project2"
        )
        
        self.assertIsNot(s1, s2)
        self.assertEqual(s2.access_token, "token2")
        self.assertEqual(s2.auth_type, AuthType.OAUTH_TOKEN)
        self.assertIsNone(s2.api_key)

    def test_reset_allows_different_auth_types(self):
        """Test that reset allows switching between auth types"""
        s1 = Session(api_key="api_key", base_url="https://test.com")
        self.assertEqual(s1.auth_type, AuthType.API_KEY)
        
        reset_session()
        
        s2 = Session(
            base_url="https://test.com",
            access_token="oauth_token",
            project_id="project_id"
        )
        self.assertEqual(s2.auth_type, AuthType.OAUTH_TOKEN)
        
        reset_session()
        
        s3 = Session(base_url="https://test.com")
        self.assertEqual(s3.auth_type, AuthType.NONE)

    def test_reset_session_allows_clean_state(self):
        """Test that reset_session creates truly independent instances"""
        s1 = Session(
            api_key="key1",
            base_url="https://test1.com",
            access_token="token1",
            project_id="project1",
            organization_id="org1",
            allow_mixed_auth=True
        )
        
        self.assertEqual(s1.api_key, "key1")
        self.assertEqual(s1.access_token, "token1")
        self.assertEqual(s1.project_id, "project1")
        self.assertEqual(s1.organization_id, "org1")
        
        reset_session()
        
        s2 = Session(base_url="https://test2.com")
        
        self.assertIsNot(s1, s2)
        self.assertIsNone(s2.api_key)
        self.assertIsNone(s2.access_token)
        self.assertIsNone(s2.project_id)
        self.assertIsNone(s2.organization_id)
        self.assertEqual(s2.auth_type, AuthType.NONE)

    def test_reset_all_instances_clears_everything(self):
        """Test that reset_all_instances clears all singleton caches"""
        s1 = Session(api_key="key1", base_url="https://test1.com")
        
        Singleton.reset_all_instances()
        
        s2 = Session(api_key="key2", base_url="https://test2.com")
        
        self.assertIsNot(s1, s2)
        self.assertEqual(s2.api_key, "key2")

    def test_singleton_cache_persists_without_reset(self):
        """Test that without reset, singleton cache persists"""
        s1 = Session(api_key="persistent_key", base_url="https://test.com")
        
        s2 = Session(api_key="ignored_key", base_url="https://ignored.com")
        
        self.assertIs(s1, s2)
        self.assertEqual(s2.api_key, "persistent_key")
        self.assertEqual(s2.base_url, "https://test.com")

    def test_reset_does_not_affect_other_sessions(self):
        """Test that reset only affects Session class singleton"""
        s1 = Session(api_key="key1", base_url="https://test1.com")
        
        reset_session()
        
        s2 = Session(api_key="key2", base_url="https://test2.com")
        
        self.assertIsNot(s1, s2)
        self.assertNotEqual(s1.api_key, s2.api_key)


class TestSingletonResetSequence(unittest.TestCase):
    """
    Tests that simulate the sequence of tests running to verify isolation.
    
    python -m unittest pygeai.tests.auth.test_singleton_reset.TestSingletonResetSequence
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_session()

    def tearDown(self):
        """Clean up test fixtures"""
        reset_session()

    def test_sequence_1_oauth_session(self):
        """Simulates a test creating OAuth session"""
        session = Session(
            base_url="https://test.com",
            access_token="oauth_token",
            project_id="project_id"
        )
        
        self.assertEqual(session.auth_type, AuthType.OAUTH_TOKEN)
        self.assertEqual(session.access_token, "oauth_token")

    def test_sequence_2_api_key_session(self):
        """Simulates next test creating API key session - should not see OAuth"""
        session = Session(
            api_key="api_key",
            base_url="https://test.com"
        )
        
        self.assertEqual(session.auth_type, AuthType.API_KEY)
        self.assertEqual(session.api_key, "api_key")
        self.assertIsNone(session.access_token)

    def test_sequence_3_no_auth_session(self):
        """Simulates test creating session with no auth - should not see previous auth"""
        session = Session(base_url="https://test.com")
        
        self.assertEqual(session.auth_type, AuthType.NONE)
        self.assertIsNone(session.api_key)
        self.assertIsNone(session.access_token)

    def test_sequence_4_different_oauth_session(self):
        """Simulates test creating different OAuth session - should not see previous"""
        session = Session(
            base_url="https://test.com",
            access_token="different_token",
            project_id="different_project"
        )
        
        self.assertEqual(session.auth_type, AuthType.OAUTH_TOKEN)
        self.assertEqual(session.access_token, "different_token")
        self.assertEqual(session.project_id, "different_project")


if __name__ == '__main__':
    unittest.main()
