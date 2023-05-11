// Utils

const options = {
  month: 'numeric',
  day: 'numeric',
  hour: 'numeric',
  minute: 'numeric',
  second: 'numeric',
};

function formatTime(timeString) {
  const parsedDate = new Date(timeString);
  const date = new Date(parsedDate.getTime() - (new Date().getTimezoneOffset() * 60000));
  return date.toLocaleDateString('cs', options);
}

export function prettyDate(dateStr) {
  return formatTime(dateStr);
}

export default {};
