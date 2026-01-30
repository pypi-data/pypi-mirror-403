/* global inherits, AlertBox, gettext, getSuperClass */
var ErrorsAlert = function () {
  AlertBox.call(this);
  this._errors = null;
};
inherits(ErrorsAlert, AlertBox);

ErrorsAlert.prototype.formatErrorList = function (errors) {
  var div = this.makeElement('div')
  div.append('<div class="mb-1">' + gettext('Please fix these errors:') + '</div>');
  var ul = this.makeElement('ul')
  div.append(ul);
  $.each(errors, function (_idx, item) {
    ul.append('<li>' + item + '</li>');
  });
  return div;
};

ErrorsAlert.prototype.formatErrors = function (errors) {
  if (typeof errors === 'string') return $('<div>' + errors + '</div>');
  if (errors.constructor === [].constructor) {
    if (errors.length === 0) return gettext('Sorry, something wrong happened.');
    if (errors.length === 1) return errors[0];
    return this.formatErrorList(errors);
  }
  if ('html' in errors) return errors;
  return gettext('Sorry, something wrong happened');
};

ErrorsAlert.prototype.showErrors = function (errors) {
  var content = this.formatErrors(errors);
  this.setContent(content)
  this.show();
}

ErrorsAlert.prototype.setErrors = function (errors) {
  if (!errors || errors.length === 0) {
    this._errors = null;
    return
  }

  this._errors = errors;

  if (!this._element) return;

  this.showErrors(errors);
}

ErrorsAlert.prototype.createDom = function () {
  var superClass = getSuperClass(ErrorsAlert);
  superClass.createDom.call(this);
  if (!this._errors) return;
  this.showErrors(this._errors);
}
