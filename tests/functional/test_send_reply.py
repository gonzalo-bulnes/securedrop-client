"""
Functional tests for sending replies in the SecureDrop client.

The tests are based upon the client testing descriptions here:
https://github.com/freedomofpress/securedrop-client/wiki/Test-plan#basic-client-testing
"""
import pytest
from flaky import flaky
from PyQt5.QtCore import Qt

from tests.conftest import TIME_CLICK_ACTION, TIME_RENDER_CONV_VIEW, TIME_RENDER_SOURCE_LIST


@flaky
@pytest.mark.vcr()
def test_send_reply_to_source(functional_test_logged_in_context, qtbot, mocker):
    """
    Verify that a reply shows up in the conversation view when a reply is sent.
    """
    gui, controller = functional_test_logged_in_context

    def check_for_sources():
        assert len(list(gui.main_view.source_list.source_items.keys()))

    # Select the first source in the source list
    qtbot.waitUntil(check_for_sources, timeout=TIME_RENDER_SOURCE_LIST)
    source_ids = list(gui.main_view.source_list.source_items.keys())
    first_source_item = gui.main_view.source_list.source_items[source_ids[0]]
    first_source_widget = gui.main_view.source_list.itemWidget(first_source_item)
    qtbot.mouseClick(first_source_widget, Qt.LeftButton)
    qtbot.wait(TIME_CLICK_ACTION)

    def check_for_conversation():
        assert gui.main_view.view_layout.itemAt(0)
        assert gui.main_view.view_layout.itemAt(0).widget()

    # Get the selected source conversation
    qtbot.waitUntil(check_for_conversation, timeout=TIME_RENDER_CONV_VIEW)
    conversation = gui.main_view.view_layout.itemAt(0).widget()

    # Focus on the reply box and type a message
    qtbot.mouseClick(conversation.reply_box.text_edit, Qt.LeftButton)
    qtbot.wait(TIME_CLICK_ACTION)
    qtbot.keyClicks(conversation.reply_box.text_edit, "Hello, world!")

    # Send the reply and wait until `reply_sent` signal is triggered
    with qtbot.waitSignal(conversation.reply_box.reply_sent):
        qtbot.mouseClick(conversation.reply_box.send_button, Qt.LeftButton)
        qtbot.wait(TIME_CLICK_ACTION)

    # Ensure the last widget in the conversation view contains the text we just typed
    last_msg_id = list(conversation.conversation_view.current_messages.keys())[-1]
    last_msg = conversation.conversation_view.current_messages[last_msg_id]
    assert last_msg.message.text() == "Hello, world!"

    # Clean up: delete the last source with the reply
    source_count = gui.main_view.source_list.count()
    controller.delete_source(conversation.conversation_title_bar.source)

    def check_source_list():
        # Confirm there is now only one source in the client list.
        assert gui.main_view.source_list.count() == source_count - 1

    qtbot.waitUntil(check_source_list, timeout=TIME_RENDER_SOURCE_LIST)
