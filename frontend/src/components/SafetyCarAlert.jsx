export default function SafetyCarAlert({ flag }) {
  if (flag !== 'sc') return null;
  return (
    <div className="sc-alert">
      <div className="ico">🚨</div>
      <div>
        <b>SAFETY CAR DEPLOYED</b>
        <span>Strategy recalculating — see the Strategy tab for the updated recommendation.</span>
      </div>
    </div>
  );
}
