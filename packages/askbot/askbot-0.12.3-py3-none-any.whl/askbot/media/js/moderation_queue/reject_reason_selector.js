/* global WrappedElement, inherits, SelectBox, askbot, gettext, setupButtonEventHandlers */
var RejectReasonSelector = function () {
  WrappedElement.call(this);
  this._selectedReasonId = null;
};
inherits(RejectReasonSelector, WrappedElement);

RejectReasonSelector.prototype.setMenu = function (menu) {
  this._menu = menu;
};

RejectReasonSelector.prototype.getMenu = function () {
  return this._menu;
};

RejectReasonSelector.prototype.reset = function () {
  this._selectedReasonId = null;
  this._selectBox.clearSelection();
};

RejectReasonSelector.prototype.addReason = function (data) {
  var id = data.reason_id;
  var title = data.title;
  var details = data.details;
  this._selectBox.addItem(id, title, details);
};

RejectReasonSelector.prototype.updateReason = function (data) {
  var item = this._selectBox.getItem(data.reason_id);
  item.setName(data.title);
  item.setDescription(data.details);
};

RejectReasonSelector.prototype.startEditingReason = function () {
  var data = this._selectBox.getSelectedItemData();
  this._selectedReasonId = data.id;
  var menu = this.getMenu();
  menu.setState('edit');
  menu.getEditor().setInputs({
    title: data.title,
    reason_id: data.id,
    details: data.details
  });
};

RejectReasonSelector.prototype.resetSelectedReasonId = function () {
  this._selectedReasonId = null;
};

RejectReasonSelector.prototype.getSelectedReasonId = function () {
  return this._selectedReasonId;
};

RejectReasonSelector.prototype.startDeletingReason = function () {
  var selectBox = this._selectBox;
  var data = selectBox.getSelectedItemData();
  var reason_id = data.id;
  var me = this;
  if (data.id) {
    $.ajax({
      type: 'POST',
      dataType: 'json',
      cache: false,
      url: askbot.urls.delete_post_reject_reason,
      data: {reason_id: reason_id},
      success: function (data) {
        if (data.success) {
          selectBox.removeItem(reason_id);
          me._editButton.hide();
          me._deleteButton.hide();
          var menu = me.getMenu();
          menu.getTopMenu().removeReason(reason_id);
        } else {
          me.setSelectorErrors(data.message);
        }
      }
    });
  } else {
    me.setSelectorErrors(gettext('A reason must be selected to delete one.'));
  }
};

RejectReasonSelector.prototype.getReasonsCount = function () {
  return this._selectBox.getItemCount();
};

RejectReasonSelector.prototype.createDom = function () {
  this._element = this.makeElement('div');

  // create the select box
  var selectBox = new SelectBox();
  this._element.append(selectBox.getElement());
  var me = this;
  selectBox.setSelectHandler(function() {
    me._editButton.show();
    me._deleteButton.show();
  });
  $.each(askbot.data.postRejectReasons, function(_idx, item) {
    selectBox.addItem(item.id, item.title, item.description);
  });
  this._selectBox = selectBox;

  // create the buttons
  var div = this.makeElement('div');
  this._element.append(div);

  // edit button
  var editButton = this.makeElement('button');
  editButton.addClass('btn');
  editButton.text(gettext('Edit this reason'));
  editButton.hide();
  div.append(editButton);
  setupButtonEventHandlers(editButton, function () { me.startEditingReason() });
  this._editButton = editButton;

  // delete button
  var deleteButton = this.makeElement('button');
  deleteButton.addClass('btn');
  deleteButton.text(gettext('Delete this reason'));
  deleteButton.hide();
  div.append(deleteButton);
  setupButtonEventHandlers(deleteButton, function () { me.startDeletingReason() });
  this._deleteButton = deleteButton;

  // add reason button
  var addReasonButton = this.makeElement('button');
  addReasonButton.addClass('btn');
  addReasonButton.text(gettext('Add a new reason'));
  div.append(addReasonButton);
  setupButtonEventHandlers(addReasonButton, function () {
    me.getMenu().setState('add-new-reason');
  });
};
