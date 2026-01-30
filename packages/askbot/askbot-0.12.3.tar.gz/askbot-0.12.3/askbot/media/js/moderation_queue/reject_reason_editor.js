/* global WrappedElement, inherits, setupButtonEventHandlers, gettext, askbot */
var RejectReasonEditor = function () {
  WrappedElement.call(this);
  this._menu = null;
  this._titleInput = null;
  this._detailsInput = null;
};
inherits(RejectReasonEditor, WrappedElement);

RejectReasonEditor.prototype.setMenu = function (menu) {
  this._menu = menu;
};

RejectReasonEditor.prototype.getMenu = function () {
  return this._menu;
};

RejectReasonEditor.prototype.reset = function () {
  if (this._titleInput) {
    this._titleInput.val('');
  }
  if (this._detailsInput) {
    this._detailsInput.val('');
  }
};

RejectReasonEditor.prototype.setInputs = function (inputs) {
  this._titleInput.val(inputs.title);
  this._detailsInput.val(inputs.details);
  if (inputs.reason_id) {
    this._selectedReasonId = inputs.reason_id;
  }
};

RejectReasonEditor.prototype.getInputs = function () {
  return {
    title: $.trim($(this._titleInput).val()),
    details: $.trim($(this._detailsInput).val()),
    reason_id: this._selectedReasonId
  }
};

RejectReasonEditor.prototype.checkInputs = function () {
  var values = this.getInputs();
  var errors = [];
  if (values.title === '') {
    errors.push(gettext('Please provide description.'));
  }
  if (values.details === '') {
    errors.push(gettext('Please provide details.'));
  }
  return errors
};

RejectReasonEditor.prototype.focus = function () {
  this._titleInput.focus();
};

RejectReasonEditor.prototype.cancelEditingReason = function () {
  this.reset();
  var menu = this.getMenu();
  menu.clearErrors();
  if (menu.getReasonsCount() === 0) {
    menu.reset();
    menu.hide();
  } else {
    menu.setState('select');
  }
};

RejectReasonEditor.prototype.startSavingReason = function () {
  var errors = this.checkInputs();
  if (errors.length > 0) {
    this.getMenu().setErrors(errors);
    return;
  }

  var me = this;
  var reasonData = this.getInputs();
  $.ajax({
    type: 'POST',
    dataType: 'json',
    cache: false,
    url: askbot.urls.save_post_reject_reason,
    data: reasonData,
    success: function (result) {
      if (result.success) {
        var menu  = me.getMenu();
        menu.setReason(result, !reasonData.reason_id);
        menu.clearErrors();
        me.getMenu().setState('select');
      } else {
        me.getMenu().setErrors(result.message);
      }
    }
  });
};

RejectReasonEditor.prototype.startEditingReason = function () {
  var data = this._select_box.getSelectedItemData();
  var title = $(data.title).text();
  var details = data.details;
  this._titleInput.setVal(title);
  this._detailsInput.setVal(details);
  this._selected_reason_id = data.id;
  this.setState('add-new');
};

RejectReasonEditor.prototype.createDom = function () {
  this._element = this.makeElement('div class="js-reject-reason-editor"');
  var titlePlaceholder = gettext('Enter a brief description of why you are rejecting the post.');
  var titleInput = $('<input type="text" placeholder="' + titlePlaceholder + '" />');
  this._element.append(titleInput);
  this._titleInput = titleInput;

  var detailsPlaceholder = gettext('Enter details here. This text will be sent to the user.');
  var detailsInput = $('<textarea placeholder="' + detailsPlaceholder + '" />');
  this._element.append(detailsInput);
  this._detailsInput = detailsInput;

  var div = this.makeElement('div');
  this._element.append(div);

  var me = this;
  var saveBtn = $('<button class="btn">' + gettext('Save reason') + '</button>');
  div.append(saveBtn);
  setupButtonEventHandlers(saveBtn, function () { me.startSavingReason(); });

  var cancelBtn = $('<button class="btn">' + gettext('Cancel') + '</button>');
  div.append(cancelBtn);
  setupButtonEventHandlers(cancelBtn, function() { me.cancelEditingReason(); });
};
