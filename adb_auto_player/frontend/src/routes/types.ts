interface Button {
  label: string;
  callback: (...args: any[]) => void;
  active: boolean;
  alwaysEnabled?: boolean;
}
