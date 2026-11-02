using System;
using System.Runtime.InteropServices;

namespace ThesisMathTypeConversionV2
{
    [ComImport]
    [Guid("00000016-0000-0000-C000-000000000046")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface IOleMessageFilter
    {
        [PreserveSig]
        int HandleInComingCall(
            int callType,
            IntPtr taskCaller,
            int tickCount,
            IntPtr interfaceInfo);

        [PreserveSig]
        int RetryRejectedCall(
            IntPtr taskCallee,
            int tickCount,
            int rejectType);

        [PreserveSig]
        int MessagePending(
            IntPtr taskCallee,
            int tickCount,
            int pendingType);
    }

    internal sealed class OleMessageFilter :
        IOleMessageFilter,
        IDisposable
    {
        private const int ServerCallRejected = 1;
        private const int ServerCallRetryLater = 2;
        private const int PendingMessageWaitDefaultProcess = 2;
        private const int RetryDelayMilliseconds = 150;
        private const int MaximumRetryWindowMilliseconds = 10000;

        private IOleMessageFilter previousFilter;
        private bool disposed;

        private OleMessageFilter()
        {
            int status = CoRegisterMessageFilter(
                this,
                out previousFilter);
            if (status != 0)
            {
                Marshal.ThrowExceptionForHR(status);
            }
        }

        internal static IDisposable Register()
        {
            return new OleMessageFilter();
        }

        public int HandleInComingCall(
            int callType,
            IntPtr taskCaller,
            int tickCount,
            IntPtr interfaceInfo)
        {
            return 0;
        }

        public int RetryRejectedCall(
            IntPtr taskCallee,
            int tickCount,
            int rejectType)
        {
            if ((rejectType == ServerCallRejected ||
                 rejectType == ServerCallRetryLater) &&
                tickCount < MaximumRetryWindowMilliseconds)
            {
                return RetryDelayMilliseconds;
            }
            return -1;
        }

        public int MessagePending(
            IntPtr taskCallee,
            int tickCount,
            int pendingType)
        {
            return PendingMessageWaitDefaultProcess;
        }

        public void Dispose()
        {
            if (disposed)
            {
                return;
            }
            disposed = true;

            IOleMessageFilter ignored;
            int status = CoRegisterMessageFilter(
                previousFilter,
                out ignored);
            previousFilter = null;
            if (status != 0)
            {
                Marshal.ThrowExceptionForHR(status);
            }
        }

        [DllImport("ole32.dll")]
        private static extern int CoRegisterMessageFilter(
            IOleMessageFilter newFilter,
            out IOleMessageFilter oldFilter);
    }
}
