from selenium.webdriver.common.by import By

from .base import FunctionalTest

EDITH = 'edith@example.com'
ONI = 'oni@example.com'


class CollaborationTest(FunctionalTest):
    def get_rows(self):
        return self.browser.find_elements(By.CSS_SELECTOR, '#id_list_table tr')

    def test_tick_off_delete_and_share_a_private_list(self):
        # Edith logs in and starts a list
        self.log_in(EDITH)
        self.add_list_item('Buy milk')
        self.add_list_item('Buy eggs')
        self.add_list_item('Buy bread')
        list_url = self.browser.current_url

        # She bought the milk, so she ticks it off
        self.get_rows()[0].find_element(By.CSS_SELECTOR, '.item-toggle').click()
        self.wait_for(lambda: self.assertIn('item-done', self.get_rows()[0].get_attribute('class')))
        self.assertNotIn('item-done', self.get_rows()[1].get_attribute('class'))

        # She changes her mind about the eggs and deletes them
        self.get_rows()[1].find_element(By.CSS_SELECTOR, '.item-delete').click()
        self.wait_for(lambda: self.assertEqual(
            [row.text for row in self.get_rows()], ['1: Buy milk', '2: Buy bread']
        ))

        # She shares the list with her friend Oni
        self.browser.find_element(By.ID, 'id_sharee').send_keys(ONI + '\n')
        self.wait_for(lambda: self.assertIn(
            ONI, self.browser.find_element(By.ID, 'id_shared_with').text
        ))

        # She logs out; the list is now private, so a stranger can't see it
        self.log_out()
        self.browser.get(list_url)
        self.assertNotIn('Buy milk', self.browser.find_element(By.TAG_NAME, 'body').text)

        # Oni logs in and finds the list under "Shared with me"
        self.log_in(ONI)
        self.browser.find_element(By.ID, 'id_my_lists').click()
        self.wait_for(lambda: self.browser.find_element(By.ID, 'id_shared_lists'))
        shared = self.browser.find_element(By.ID, 'id_shared_lists')
        self.assertIn(EDITH, shared.text)
        shared.find_element(By.LINK_TEXT, 'Buy milk').click()

        # She can add to it, but can't delete or re-share it
        self.wait_for_row_in_list_table('1: Buy milk')
        self.add_list_item('Buy jam')
        self.assertFalse(self.browser.find_elements(By.ID, 'id_share_form'))
        self.assertFalse(self.browser.find_elements(By.ID, 'id_delete_list'))

    def test_owner_can_delete_list(self):
        self.log_in(EDITH)
        self.add_list_item('Temporary list')

        # Edith deletes the list, confirming the browser prompt
        self.browser.find_element(By.ID, 'id_delete_list').click()
        self.browser.switch_to.alert.accept()

        # She lands on My lists, which is now empty
        self.wait_for(lambda: self.assertIn(
            'List deleted.', self.browser.find_element(By.TAG_NAME, 'body').text
        ))
        self.assertIn(
            "You don't have any lists yet.",
            self.browser.find_element(By.ID, 'id_my_lists_list').text,
        )
