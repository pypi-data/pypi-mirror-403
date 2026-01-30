/**
 * will setup a bootstrap.js alert
 * programmatically
 */
var AlertBox = function () {
    WrappedElement.call(this);
    this._text = null;
};
inherits(AlertBox, WrappedElement);

AlertBox.prototype.setClass = function (classes) {
    this._classes = classes;
    if (this._element) {
        this._element.addClass(classes);
    }
};

AlertBox.prototype.setError = function (state) {
    this._is_error = state;
    if (this._element) {
        if (state === true) {
            this._element.addClass('alert-error');
        } else {
            this._element.removeClass('alert-error');
        }
    }
};

AlertBox.prototype.setText = function (text) {
    this._text = text;
    if (this._content) {
        this._content.html(text);
    }
};

AlertBox.prototype.getContent = function () {
    if (this._content) {
        return this._content;
    } else {
        this._content = this.makeElement('div');
        return this._content;
    }
};

AlertBox.prototype.setContent = function (content) {
    var container = this.getContent();
    container.empty();
    container.append(content);
};

AlertBox.prototype.addContent = function (content) {
    var container = this.getContent();
    container.append(content);
};

AlertBox.prototype.clear = function () {
    this.getContent().empty();
    this.hide();
};

AlertBox.prototype.createDom = function () {
    this._element = this.makeElement('div');
    this._element.addClass('js-alert-box');

    if (this._is_error) {
        this.setError(this._is_error);
    }

    if (this._classes) {
        this._element.addClass(this._classes);
    }

    var cancelButton = this.makeElement('button');
    cancelButton
        .addClass('js-alert-box--dismiss-button')
        .attr('data-dismiss', 'alert')
        .html('&times;');
    
    this._element.append(cancelButton);
    var me = this;
    setupButtonEventHandlers(cancelButton, function () { me.clear(); });
    this._cancel_button = cancelButton;

    this._element.append(this.getContent());
    if (this._text) {
        this.setText(this._text);
    }

    this.hide();
};
