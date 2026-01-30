/* global askbot, interpolate, ngettext */
askbot.validators = askbot.validators || {};
askbot.validators.answerValidator = function (text) {
  var minLength = askbot.settings.minAnswerBodyLength;
  text = $.trim(text);
  var textLength = text.length;
  if (minLength && (textLength < minLength)) {
    throw interpolate(
      ngettext(
        'enter > %(length)s character',
        'enter > %(length)s characters',
        minLength
      ),
      {'length': minLength},
      true
    );
  }
};
